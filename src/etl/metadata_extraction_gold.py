import typer
from pathlib import Path
from datetime import date
from typing import Optional, List
import json
import ollama
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm
import logging

app = typer.Typer()

# Set up logging
logger = logging.getLogger("contract_etl")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

def setup_file_logging(logfile: Optional[Path]):
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)


class ExtractedContractMetadata(BaseModel):
    contract_title: str = Field(..., description="Title or short name of the contract")
    contract_type: str = Field(..., description="Type of contract, e.g., Purchase Contract, MSA, SOW")
    supplier_name: str = Field(..., description="Name of the supplier/vendor")
    buyer_name: str = Field(..., description="Name of the buyer organization")
    purchase_order: Optional[str] = Field(None, description="Linked purchase order ID, order Number, if any or Contract Number")
    purchase_date: date = Field(..., description="Date the contract was signed or became effective in DD-MM-YYYY format")
    expiry_date: date = Field(..., description="Date the contract expires or ends in DD-MM-YYYY format")
    contract_description: str = Field(..., description="Very short Oneline description of the contract, if not exist create one.")
    objective: Optional[str] = Field(None, description="Stated business objective of the contract")
    scope: Optional[List[str]] = Field(default_factory=list, description="List describing the scope of the agreement")
    pricing_and_payment_terms: Optional[str] = Field(None, description="Terms related to pricing and payment schedule")
    delivery_terms: Optional[str] = Field(None, description="Conditions related to delivery, location, timelines")
    quality_assurance: Optional[str] = Field(None, description="Obligations regarding quality and handling of defects")
    confidentiality_clause: Optional[bool] = Field(False, description="Whether a confidentiality clause is present")
    termination_clause: Optional[str] = Field(None, description="Conditions under which the contract may be terminated")

class ContractMetadata(ExtractedContractMetadata):
    cwid: str = Field(..., description="CWID of the contract from the Contract Name.")


# System prompt
SYSTEM_PROMPT = """
You are a Contract Metadata Extractor.

Your job is to analyze raw contract documents and extract structured metadata in JSON format.

Use the following Pydantic model as a reference structure:

```python
class ExtractedContractMetadata(BaseModel):
    contract_title: str
    contract_type: str
    supplier_name: str
    buyer_name: str
    purchase_order: Optional[str]
    purchase_date: date
    expiry_date: date
    contract_description: str
    objective: Optional[str]
    scope: Optional[List[str]]
    pricing_and_payment_terms: Optional[str]
    delivery_terms: Optional[str]
    quality_assurance: Optional[str]
    confidentiality_clause: Optional[bool]
    termination_clause: Optional[str]

Guidelines:

- Extract all fields if present. If a field is not found, omit it or set it to null.
- The contract must have a purchase date and an expiry date.
- Dates must be in ISO format: YYYY-MM-DD.
- Date might be provided in the text. like Effective date: December 2020, which you should consider as Effective Date: 2020-12-01
- Expiry date might be provided in the text. like Expiry Date: 5 years from the Effective Date, which you should consider as Expiry Date: 2025-12-01
- Fields like scope must be a list of bullet points if multiple scopes are defined.
- For contract_type, infer the type such as "Purchase Contract", "MSA", "SOW", Framework Agreement / PO Contract etc.
- If no contract_type found in the text, set it to "Contract".
- For confidentiality_clause, return true if any confidentiality-related language exists; else false.
- For signatories, include organization names and their roles (e.g., "Buyer", "Supplier").
- Output the result as valid JSON matching the model above, with no commentary or explanation.

You will now be given the full contract document as input.
"""

def extract_metadata(contract_text: str, model: str) -> ExtractedContractMetadata:
    logger.info("Extracting metadata...")
    response = ollama.chat(
        model=model,
        format=ExtractedContractMetadata.model_json_schema(),
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': contract_text}
        ]
    )
    content = response['message']['content']
    logger.info(f"Metadata extracted as {str(content)[:100]}...")
    return ExtractedContractMetadata.model_validate_json(content)

def load_json_contract(file_path: Path) -> dict:
    logger.info(f"Loading contract from {file_path}")
    with file_path.open('r') as f:
        return json.load(f)
    

def add_cwid(metadata: ExtractedContractMetadata, file_path: Path) -> ContractMetadata:
    cwid = file_path.stem.split(".")[0]
    metadata = ContractMetadata(**metadata.model_dump(), cwid=cwid)
    logger.info(f"Added CWID {cwid} to metadata")
    return metadata

def save_metadata(metadata: ContractMetadata, destination: Path, dryrun: bool):
    output_path = destination / f"{metadata.cwid}.json"
    if not dryrun:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w') as f:
            f.write(metadata.model_dump_json(indent=2))
    logger.info(f"{'DRYRUN: ' if dryrun else ''}Saved metadata to {output_path}")

@app.command()
def main(
    source: Path = typer.Option(..., "--src", '-s',help="Source folder with contract JSONs"),
    destination: Path = typer.Option(..., "--dst", '-d', help="Destination folder for metadata JSONs"),
    dryrun: bool = typer.Option(False, help="Run without writing output"),
    model: str = typer.Option("gemma3:4b", help="Ollama model to use"),
    log_level: str = typer.Option("INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR"),
    limit: Optional[int] = typer.Option(None, help="Process only N number of files"),
    logfile: Optional[Path] = typer.Option(None, help="Path to a log file"),
):
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    setup_file_logging(logfile)

    files = list(source.glob("*.json"))
    if limit:
        files = files[:limit]
    logger.info(f"Processing {len(files)} contract(s)...")

    for file_path in tqdm(files, desc="Extracting metadata", unit="file"):
        try:
            contract_data = load_json_contract(file_path)
            contract_text = contract_data.get("text", "")
            extracted_metadata = extract_metadata(contract_text, model)
            contract_metadata = add_cwid(extracted_metadata, file_path)
            save_metadata(contract_metadata, destination, dryrun)
        except ValidationError as e:
            logger.error(f"[{file_path.name}] Validation error: {e}")
        except Exception as e:
            logger.error(f"[{file_path.name}] General error: {e}")

if __name__ == "__main__":
    app()