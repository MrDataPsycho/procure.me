import chromadb
from smart_procurement.embeeding_funcs import MixedbreadEmbeddingFunction
from smart_procurement.embeeders import MixedbreadEmbedder
from pydantic import BaseModel
import logging
from uuid import uuid4
from smart_procurement.models.cc_codes_model import CommodityCodesList
import os
import json

CACHING_COLLECTION_NAME = "cc_caching"

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    doc_id: str
    distance: float
    metadata: str

    @classmethod
    def from_chroma_response(cls, response: dict):
        doc_id = response["ids"][0][0]
        distance = response["distances"][0][0]
        metadata = response["metadatas"][0][0]
        return cls(doc_id=doc_id, distance=distance, metadata=metadata)

    def is_similar(self, threshold: float) -> bool:
        return self.distance <= threshold


async def query_result_from_caching_db(
    query: str,
    embedder_func: MixedbreadEmbeddingFunction,
    threshhold: float = 0.1,
    host: str | None = None,
    port: str | None = None,
) -> dict | None:
    if host and port:
        client = await chromadb.AsyncHttpClient(
            host=host, port=port
        )
    else:
        client = await chromadb.AsyncHttpClient(
            host=os.environ["VECTOR_DB_HOST"], port=os.environ["VECTOR_DB_PORT"]
        )
    
    collection = await client.get_collection(
        CACHING_COLLECTION_NAME,
        embedding_function=embedder_func,
    )
    response = await collection.query(
        query_texts=[query],
        include=["metadatas", "distances"],
        n_results=1,
    )
    result = SearchResult.from_chroma_response(response=response)
    if result.is_similar(threshold=threshhold):
        logger.info("Result found in caching db.")
        return result.metadata
    return None


async def add_result_to_caching_db(
    result: CommodityCodesList,
    document: str,
    embidding_func: MixedbreadEmbeddingFunction,
    host: str | None = None,
    port: str | None = None,
) -> None:
    
    if host and port:
        client = await chromadb.AsyncHttpClient(
            host=host, port=port
        )
    else:
        client = await chromadb.AsyncHttpClient(
            host=os.environ["VECTOR_DB_HOST"], port=os.environ["VECTOR_DB_PORT"]
        )

    collection = await client.get_collection(
        CACHING_COLLECTION_NAME,
        embedding_function=embidding_func,
    )
    logger.info("Adding result to Caching DB.")
    response = await collection.add(
        ids=[str(uuid4())],
        metadatas=[{"result": json.dumps(result.model_dump()["codes"])}],
        documents=[document],
    )
    logger.info(f"Result added to caching db successfully: {response}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    import asyncio

    assert load_dotenv(".envs/dev.env", override=True)
    EMB_MODEL_PATH = "models/embeddings/mxbai-embed-large-v1"
    EMBEDDER = MixedbreadEmbedder(EMB_MODEL_PATH)
    emb_func = MixedbreadEmbeddingFunction(embedder=EMBEDDER)
    query = "I want to buy keyboard and mouse for my Laptop."
    result = asyncio.run(query_result_from_caching_db(query=query,embedder_func=emb_func))
    
