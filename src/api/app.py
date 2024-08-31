from quart import Quart, request
from dotenv import load_dotenv
from smart_procurement.configurations.db_connection_config import DbConnectionModel
from smart_procurement.models.cc_codes_model import CommodityCodes
import os
from sqlmodel import create_engine, select, Session, col
from smart_procurement.embeeders import MixedbreadEmbedder
from smart_procurement.embeeding_funcs import MixedbreadEmbeddingFunction
import chromadb
import logging
from uuid import uuid5
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pathlib import Path


assert load_dotenv(".envs/dev.env", override=True)
logger = logging.getLogger(__name__)

app = Quart(__name__)
db_connection = DbConnectionModel(**os.environ)
engine = create_engine(db_connection.get_connecton_str_with_psycopg2())
EMB_MODEL_PATH = "models/embeddings/mxbai-embed-large-v1"
EMBEDDER = MixedbreadEmbedder(EMB_MODEL_PATH)
CACHING_COLLECTION_NAME = "cc_caching"
VECTOR_COLLECTION_NAME = "commodity_codes"
load_dotenv(Path(__file__).parent.parent.parent.joinpath(".envs/dev.env"))


@app.route("/api/v1/codes")
async def get_commodity_codes():
    with Session(engine) as session:
        commodity_codes = select(CommodityCodes)
        commodity_codes = session.exec(commodity_codes).all()
        return [item.model_dump() for item in commodity_codes]


async def get_codes_by_id(ids: list) -> list[CommodityCodes]:
    with Session(engine) as session:
        statement = select(CommodityCodes).where(col(CommodityCodes.l3).in_(ids))
        commodity_codes = session.exec(statement).all()
        return commodity_codes


async def query_vector_db(text: str) -> list[int]:
    client = await chromadb.AsyncHttpClient(
        host=os.environ["VECTOR_DB_HOST"], port=os.environ["VECTOR_DB_PORT"]
    )
    collection = await client.get_collection(
        VECTOR_COLLECTION_NAME,
        embedding_function=MixedbreadEmbeddingFunction(embedder=EMBEDDER),
    )
    logger.info(f"Quering the vector db with query: {text}")
    result = await collection.query(
        query_texts=[text],
        include=["documents", "metadatas", "distances"],
        n_results=3,
    )

    ids = result.get("ids")
    logger.info(f"Found following ids: {ids}")
    return [int(item) for item in ids[0]]


async def add_result_to_caching_db(result: dict, document: str) -> None:
    client = await chromadb.AsyncHttpClient(host="localhost", port=8011)
    collection = await client.get_collection(
        CACHING_COLLECTION_NAME,
        embedding_function=MixedbreadEmbeddingFunction(embedder=EMBEDDER),
    )
    logger.info("Adding result to Caching DB.")
    response = await collection.add(
        ids=[str(uuid5())],
        metadatas=[{"result": result}],
        documents=[document],
    )
    logger.info(f"Result added to caching db successfully: {response}")


class SearchResult(BaseModel):
    doc_id: str
    distance: float
    metadata: dict

    @classmethod
    def from_chroma_response(cls, response: dict):
        doc_id = response["ids"][0][0]
        distance = response["distances"][0][0]
        metadata = response["metadatas"][0][0]
        return cls(doc_id=doc_id, distance=distance, metadata=metadata)

    def is_similar(self, threshold: float) -> bool:
        return self.distance <= threshold


async def query_result_from_caching_db(query: str, threshhold: 0.1) -> dict | None:
    client = await chromadb.AsyncHttpClient(host="localhost", port=8011)
    collection = await client.get_collection(
        CACHING_COLLECTION_NAME,
        embedding_function=MixedbreadEmbeddingFunction(embedder=EMBEDDER),
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


@app.route("/api/v1/search", methods=["POST"])
async def search():
    default_response = {"original": search_input, "result": None}

    data = await request.json
    search_input: str = data.get("search_input", "")
    logger.info(f"Got Search Input: {search_input}")

    if not search_input:
        return {"error": "No search input provided"}, 400

    result = await query_result_from_caching_db(query=search_input)
    if result:
        return {"original": search_input, "result": result}

    response = await query_vector_db(search_input)
    ids = [int(item) for item in response[0][0]]
    if ids:
        data: list[CommodityCodes] = await get_codes_by_id(ids=ids)
        response = [item.model_dump() for item in data]
        await add_result_to_caching_db(result=response, document=search_input)
        return {"original": search_input, "result": response}
    return default_response


if __name__ == "__main__":
    app.run()
