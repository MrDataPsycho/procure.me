import json
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine
from procureme.dbmodels.doc_summery import ContractSummary
from procureme.configurations.app_configs import Settings
import logging

logger = logging.getLogger("contract_etl")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(console_handler)


settings = Settings()
engine = create_engine(settings.pg_database_url)


# -------------------
# Load and insert summaries
# -------------------
def load_summaries(json_dir: Path):
    json_files = list(json_dir.glob("*.json"))
    with Session(engine) as session:
        for file in json_files:
            with open(file, "r") as f:
                data = json.load(f)
            
            summary = ContractSummary(
                cwid=data["cwid"],
                summary_short=data.get("short_summary"),
                summary_medium=data.get("medium_summary"),
                summary_long=data.get("long_summary"),
                )

            session.merge(summary)  # upsert behavior
        session.commit()
        logger.info(f"Inserted {len(json_files)} contract summaries.")

if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    load_summaries(Path("data/gold/summaries"))
