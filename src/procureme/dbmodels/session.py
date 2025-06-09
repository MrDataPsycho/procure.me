from sqlmodel import SQLModel, Field, Column
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from enum import StrEnum

class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(SQLModel):
    role: ChatRole  # "user" or "assistant"
    content: str
    timestamp: str

    def to_llm_format(self) -> dict[str, str]:
        return {
            "role": self.role.value,
            "content": self.content
        }

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    label: str
    messages: List[dict] = Field(sa_column=Column(MutableList.as_mutable(JSONB)), default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


if __name__ == "__main__":
    from sqlmodel import create_engine
    from procureme.configurations.app_configs import Settings

    settings = Settings()
    engine = create_engine(settings.pg_database_url, echo=True)
    SQLModel.metadata.create_all(engine)
