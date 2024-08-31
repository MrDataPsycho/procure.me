from sqlmodel import Session, col, select
from smart_procurement.models.cc_codes_model import CommodityCodesList, CommodityCodes


async def get_codes_by_id(ids: list, engine) -> CommodityCodesList:
    with Session(engine) as session:
        statement = select(CommodityCodes).where(col(CommodityCodes.l3).in_(ids))
        commodity_codes = session.exec(statement).all()
        return CommodityCodesList(codes=commodity_codes)
