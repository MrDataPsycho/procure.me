from sqlmodel import SQLModel, Field
from smart_procurement.configurations.db_connection_config import DbConnectionModel
from pydantic import BaseModel


class CommodityCodes(SQLModel, table=True):
    __tablename__ = "commodity_codes"
    l1: int
    l1_desc: str
    l2: int
    l2_desc: str
    l3: int = Field(default=None, primary_key=True)
    l3_desc: str


class CommodityCodesList(BaseModel):
    codes: list[CommodityCodes]


if __name__ == "__main__":
    from sqlmodel import SQLModel, create_engine, select, Session
    from dotenv import load_dotenv
    import os

    assert load_dotenv(".envs/dev.env", override=True)

    db_connection = DbConnectionModel(**os.environ)

    # Database configuration
    DATABASE_URL = db_connection.get_connection_str()
    engine = create_engine(db_connection.get_connecton_str_with_psycopg2())
    with Session(engine) as session:
        commodity_codes = select(CommodityCodes)
        commodity_codes = session.exec(commodity_codes).all()
        code_list = CommodityCodesList(codes=commodity_codes)
        print(code_list)
