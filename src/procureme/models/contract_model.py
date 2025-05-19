from uuid import uuid4
from pydantic import BaseModel, Field
from typing import List

class ParsedDocumentParts(BaseModel):
    id_: str
    text: str
    part: str

class ParsedDocument(BaseModel):
    id_: str = Field(default_factory=lambda: str(uuid4()))
    total_pages: int
    file_name: str
    text: str
    parts: List[ParsedDocumentParts]
