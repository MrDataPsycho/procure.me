from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: UUID
    query: str

class SourceDocument(BaseModel):
    document_title: str
    section_text: str

class ChatResponse(BaseModel):
    response: str
    success: bool = False
    sources: Optional[List[SourceDocument]] = []


class EnvInfo(BaseModel):
    env: str
    file_exists: bool
    dir_list: list
    file_path: str


class ChatSessionSummary(BaseModel):
    id: UUID
    label: str
    created_at: datetime
    updated_at: datetime