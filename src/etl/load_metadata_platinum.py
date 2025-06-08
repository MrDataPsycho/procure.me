import json
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine
from procureme.dbmodels.doc_metadata import ContractMetadata
from procureme.configurations.app_configs import Settings
import logging

logger = logging.getLogger("contract_etl")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)



def load_metadata_files(metadata_dir: str):
    metadata_files = Path(metadata_dir).glob("*.json")
    for file_path in metadata_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                yield ContractMetadata.model_validate(data)
            except Exception as e:
                print(f"❌ Failed to load {file_path.name}: {e}")

def main():
    settings = Settings()
    engine = create_engine(settings.pg_database_url, echo=True)

    # Create table if not exists
    SQLModel.metadata.create_all(engine)

    metadata_dir = "data/gold/metadata"

    with Session(engine) as session:
        for contract in load_metadata_files(metadata_dir):
            logger.info(f"✅ Inserting {contract.cwid}")
            session.add(contract)
        session.commit()
        logger.info("🎉 All metadata inserted successfully.")

if __name__ == "__main__":
    main()
