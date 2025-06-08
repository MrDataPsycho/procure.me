from typing import List, Optional
from datetime import date
from sqlmodel import SQLModel, Field
from sqlmodel import SQLModel
from sqlalchemy.dialects.postgresql import JSONB

class ContractMetadata(SQLModel, table=True):
    __tablename__ = "contract_metadata"
    cwid: str = Field(..., primary_key=True)  
    contract_title: str
    contract_type: str
    supplier_name: str
    buyer_name: str
    purchase_order: Optional[str] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    contract_description: Optional[str] = None
    objective: Optional[str] = None
    scope: Optional[List[str]] = Field(sa_type=JSONB, default_factory=list)
    pricing_and_payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    quality_assurance: Optional[str] = None
    confidentiality_clause: Optional[bool] = False
    termination_clause: Optional[str] = None