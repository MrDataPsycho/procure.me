from sqlmodel import SQLModel, create_engine
from procureme.configurations.app_configs import Settings



setting = Settings()
engine = create_engine(setting.pg_database_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()



