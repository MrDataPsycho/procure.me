from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from procureme.clients.ollama_embedder import OllamaEmbeddingClient
from procureme.vectordb.lance_vectordb import LanceDBVectorStore
from pathlib import Path
from llama_index.llms.ollama import Ollama
from procureme.agents.ragagent import RAGChatAgent
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("ContractApp")


# ----------- FastAPI setup -----------
app = FastAPI(
    title="RAG Chat API",
    description="API for interacting with RAG-based agent using LanceDB and Ollama",
    version="1.0.0",
)

# ----------- Request/Response Schemas -----------
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    response: str
    success: bool
    sources: Optional[list]


# ----------- Load dependencies -----------
# Initialize embedding client
embed_client = OllamaEmbeddingClient()
# Set DB path and table
DBPATH = Path("vectordb").joinpath("contracts.db")
VECTORDB_TABLE = "contracts_naive"
# Initialize vector store
VECTOR_STORE = LanceDBVectorStore(db_path=DBPATH, table_name=VECTORDB_TABLE, embedding_client=embed_client)
# Initialize Ollama LLM client
LLM_CLIENT = Ollama(model="gemma3:4b", request_timeout=120.0)
# Build agent
AGENT = RAGChatAgent(llm_client=LLM_CLIENT, vector_store=VECTOR_STORE)


# ----------- API Endpoint -----------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        result = AGENT.chat(query=request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))