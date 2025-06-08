from quart import Quart, request
from dotenv import load_dotenv
from procureme.configurations.db_connection_config import DbConnectionModel
from procureme.models.cc_codes_model import CommodityCodes
import os
from sqlmodel import create_engine, select, Session
from procureme.embeeders import MixedbreadEmbedder
from procureme.embeeding_funcs import MixedbreadEmbeddingFunction
from procureme.interfaces.retriver_interface import (
    query_vector_db,
    QueryResultList,
)
from procureme.interfaces.rdb_interface import get_codes_by_id
import logging
import os
from dotenv import load_dotenv
from pathlib import Path


logger = logging.getLogger(__name__)
assert load_dotenv(
    Path(__file__).parent.parent.parent.joinpath(".envs", "dev.env"), override=True
)


app = Quart(__name__)
db_connection = DbConnectionModel(**os.environ)
engine = create_engine(db_connection.get_connecton_str_with_psycopg2())
EMB_MODEL_PATH = "models/embeddings/mxbai-embed-large-v1"
EMBEDDER = MixedbreadEmbedder(EMB_MODEL_PATH)
EMB_FUNC = MixedbreadEmbeddingFunction(embedder=EMBEDDER)
VECTOR_COLLECTION_NAME = "commodity_codes"


@app.route("/api/v1/codes")
async def get_commodity_codes():
    with Session(engine) as session:
        commodity_codes = select(CommodityCodes)
        commodity_codes = session.exec(commodity_codes).all()
        return [item.model_dump() for item in commodity_codes]


@app.route("/api/v1/search", methods=["POST"])
async def search():
    data = await request.json
    search_input: str = data.get("search_input", "")
    logger.info(f"Got Search Input: {search_input}")
    default_response = {"original": search_input, "result": None}

    if not search_input:
        return {"error": "No search input provided"}, 400

    # result = await query_result_from_caching_db(query=search_input)
    # if result:
    #     return {"original": search_input, "result": result}

    response: QueryResultList = await query_vector_db(search_input, embeeder=EMB_FUNC)
    ids = response.ids
    logger.info(f"Id matched {ids}")
    if ids:
        commodity_codes = await get_codes_by_id(ids=ids, engine=engine)
        response = commodity_codes.model_dump()
        # await add_result_to_caching_db(result=response, document=search_input)
        return {"query": search_input, "response_data": response["codes"]}
    return default_response


if __name__ == "__main__":
    app.run()
