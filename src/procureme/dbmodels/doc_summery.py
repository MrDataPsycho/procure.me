from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ContractSummary(SQLModel, table=True):
    __tablename__ = "contract_summaries"

    cwid: str = Field(primary_key=True, description="Contract ID (CWID), linked to metadata table")
    summary_short: str = Field(..., description="Short version of the contract summary")
    summary_medium: str = Field(..., description="Medium version of the contract summary")
    summary_long: str = Field(..., description="Long version of the contract summary")
    generated_at: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of summary generation")
