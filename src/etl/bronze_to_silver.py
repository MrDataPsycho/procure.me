from llama_index.readers.file import PyMuPDFReader
from llama_index.core import Document
from pathlib import Path
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional, List
import logging
from tqdm import tqdm
from procureme.models import ParsedDocument, ParsedDocumentParts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('document_pipeline')

# Define paths
DATA_PATH = Path("data")
CONTRACTS_PATH = DATA_PATH.joinpath("raw", "contracts")
SILVER_PATH = DATA_PATH.joinpath("silver", "contracts")



class DocumentParser:
    """Parse a document into a list of documents. But also preserved the metadata and original document as markdown."""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.ir = Optional[Document]  # Intermediate representation
        self.write_file_name = f"{file_path.name}.json"

    def parse_to_markdown(self) -> List[Document]:
        loader = PyMuPDFReader()
        documents = loader.load(file_path=self.file_path)
        return documents

    def parse(self) -> ParsedDocument:
        try:
            documents = self.parse_to_markdown()
            total_page = len(documents)
            file_name = self.file_path.name
            text = []
            parts = []
            for item in documents:
                page_number = item.metadata.get("page_number", item.metadata.get("source", "unknown"))
                part = ParsedDocumentParts(id_=item.id_, text=item.text, part=f"part - {page_number}")
                parts.append(part)
                text.append(item.text + "\n" + f"page - [{page_number}]\n")
            parsed_document = ParsedDocument(total_pages=total_page, file_name=file_name, text="".join(text), parts=parts)
            self.ir = parsed_document
            return self.ir
        except Exception as e:
            logger.error(f"Error parsing document {self.file_path}: {e}")
            raise


    def save(self, file_path: Path) -> bool:
        if self.ir is None:
            raise ValueError("Document is not parsed yet.")
        
        try:
            # Ensure directory exists
            file_path.mkdir(parents=True, exist_ok=True)
            
            write_path = file_path.joinpath(self.write_file_name)
            with open(write_path, "w", encoding="utf-8") as f:
                json_data = self.ir.model_dump_json(indent=4)
                f.write(json_data)
            logger.info(f"Document saved to {write_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving document to {file_path}: {e}")
            return False


class DocumentProcessingPipeline:
    """Pipeline to process all documents in a directory and save them to another directory."""
    
    def __init__(self, input_dir: Path, output_dir: Path, file_extensions: List[str] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_extensions = file_extensions or ['.pdf']
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_files_to_process(self) -> List[Path]:
        """Get list of files to process based on extensions."""
        files = []
        for ext in self.file_extensions:
            files.extend(list(self.input_dir.glob(f"*{ext}")))
        return files
        
    def process_file(self, file_path: Path) -> bool:
        """Process a single file."""
        try:
            parser = DocumentParser(file_path=file_path)
            parser.parse()
            return parser.save(file_path=self.output_dir)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return False


    def run(self) -> dict:
        """Run the pipeline on all files in the input directory."""
        files = self.get_files_to_process()
        
        if not files:
            logger.warning(f"No files found with extensions {self.file_extensions} in {self.input_dir}")
            return {"total": 0, "processed": 0, "failed": 0}
            
        logger.info(f"Found {len(files)} files to process")
        
        results = {
            "total": len(files),
            "processed": 0,
            "failed": 0,
            "failed_files": []
        }
        
        for file_path in tqdm(files, desc="Processing documents"):
            success = self.process_file(file_path)
            if success:
                results["processed"] += 1
            else:
                results["failed"] += 1
                results["failed_files"].append(str(file_path))
                
        logger.info(f"Pipeline complete. Processed {results['processed']} files. Failed: {results['failed']} files.")
        return results


def main():
    """Main entry point for the document processing pipeline."""
    try:
        # Create and run the pipeline
        pipeline = DocumentProcessingPipeline(input_dir=CONTRACTS_PATH, output_dir=SILVER_PATH)
        results = pipeline.run()
        
        # Print summary
        print("\nPipeline Results Summary:")
        print(f"Total files: {results['total']}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Failed: {results['failed']}")
        
        if results['failed'] > 0:
            print("\nFailed files:")
            for failed_file in results['failed_files']:
                print(f" - {failed_file}")
                
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


if __name__ == "__main__":
    main()