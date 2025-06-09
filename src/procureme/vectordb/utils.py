from pathlib import Path
from procureme.vectordb.lance_vectordb import LanceDBVectorStore
from procureme.clients.ollama_embedder import OllamaEmbeddingClient
from procureme.clients.openai_embedder import OpenAIEmbeddingClient
from logging import getLogger
import os

logger = getLogger(__name__)

def get_vector_store():
    table_name = os.getenv("VECTOR_TABLE", "contracts_naive")
    vector_db_path = Path("vectordb").joinpath("contracts.db")
    if table_name == "contracts_naive":
        emb_client = OllamaEmbeddingClient()
        vector_store = LanceDBVectorStore(
            db_path=vector_db_path, 
            table_name=table_name, 
            embedding_client=emb_client
        )
        logger.info("Vector DB Loaded successfully.")
        return vector_store
    emb_client = OpenAIEmbeddingClient()
    vector_store = LanceDBVectorStore(
        db_path=vector_db_path, 
        table_name=table_name, 
        embedding_client=emb_client
    )
    logger.info("Vector DB Loaded successfully.")
    return vector_store


if __name__ == "__main__":
    from procureme.configurations.app_configs import Settings
    settings = Settings()
    os.environ["VECTOR_TABLE"] = "contracts_oai"
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    vector_store = get_vector_store()
    print(vector_store.get_stats())