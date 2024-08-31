from pydantic import BaseModel
import os
import chromadb
from smart_procurement.embeeding_funcs import MixedbreadEmbeddingFunction
import logging

VECTOR_COLLECTION_NAME = "commodity_codes"

logger = logging.getLogger(__name__)


class QueryResultMetadata(BaseModel):
    l1: int
    l1_desc: str
    l2: int
    l2_desc: str


class QueryResult(BaseModel):
    id: int
    metadata: QueryResultMetadata
    distance: float
    document: str


class QueryResultList(BaseModel):
    results: list[QueryResult]

    def get_ids_form_list(self):
        return [item.id for item in self.results]

    @property
    def ids(self):
        return self.get_ids_form_list()


def parse_query_result(response: dict) -> list[QueryResult]:
    result = []
    for _id, metadata, distance, document in zip(
        response["ids"][0],
        response["metadatas"][0],
        response["distances"][0],
        response["documents"][0],
    ):
        query_result = QueryResult(
            id=_id,
            metadata=metadata,
            distance=distance,
            document=document,
        )
        result.append(query_result)
    return result


async def query_vector_db(
    text: str,
    embeeder_func: MixedbreadEmbeddingFunction,
    host: str | None = None,
    port: str | None = None,
) -> QueryResultList:
    if host and port:
        client = await chromadb.AsyncHttpClient(
            host=host, port=port
        )
    else:
        client = await chromadb.AsyncHttpClient(
            host=os.environ["VECTOR_DB_HOST"], port=os.environ["VECTOR_DB_PORT"]
        )
    collection = await client.get_collection(
        VECTOR_COLLECTION_NAME,
        embedding_function=embeeder_func,
    )
    logger.info(f"Quering the vector db with query: {text}")
    result = await collection.query(
        query_texts=[text],
        include=["documents", "metadatas", "distances"],
        n_results=3,
    )
    parsed_result = parse_query_result(result)
    return QueryResultList(results=parsed_result)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import asyncio
    from smart_procurement.embeeders import MixedbreadEmbedder

    assert load_dotenv(".envs/dev.env", override=True)
    EMB_MODEL_PATH = "models/embeddings/mxbai-embed-large-v1"
    EMBEDDER = MixedbreadEmbedder(EMB_MODEL_PATH)
    embeeder_func = MixedbreadEmbeddingFunction(embedder=EMBEDDER)
    query = "I want to buy keyboard and mouse for my Laptop."
    result = asyncio.run(query_vector_db(text=query, embeeder_func=embeeder_func))
    print(result.model_dump_json())
    print(result.ids)
