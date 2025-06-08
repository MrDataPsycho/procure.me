from pydantic_settings import BaseSettings
import os
from pathlib import Path
from sqlmodel import Session, create_engine
import logging

logger = logging.getLogger(__name__)


DEFAULT_ENV_FILE = Path(".env")

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str


    @property
    def pg_database_url(self):
        host_system = os.getenv("HOST_SYSTEM")
        if host_system == "container":
            logger.info("Running in container")
            self.POSTGRES_HOST = "postgres"
            return (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = DEFAULT_ENV_FILE if os.getenv("RUNTIME_ENV", "local") == "local" else None
        extra = "ignore"


def get_session():
    settings = Settings()
    engine = create_engine(settings.pg_database_url, echo=True)
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    print(DEFAULT_ENV_FILE)
    settings = Settings()
    print(settings.pg_database_url)