from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime, timezone
import os

from procureme.dbmodels.session import ChatSession, ChatMessage, ChatRole
from .schema import ChatRequest, ChatResponse, SourceDocument, EnvInfo, ChatSessionSummary
from procureme.configurations.app_configs import get_session, DEFAULT_ENV_FILE
from procureme.agents.orchrastrator import OrchrastratorAgent
from procureme.clients.openai_chat import OpenAIClient
from procureme.configurations.aimodels import ChatModelSelection
from procureme.configurations.app_configs import Settings

import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])
setting = Settings()
client = OpenAIClient(setting.OPENAI_API_KEY, ChatModelSelection.GPT4_1_NANO)
orchrastrator_agent = OrchrastratorAgent(client)


@router.get("/runtime-env")
def get_runtime_environment():
    runtime_env = os.getenv("RUNTIME_ENV", "remote")
    envfile_exists = os.path.exists(DEFAULT_ENV_FILE)
    env_dir = DEFAULT_ENV_FILE.parent
    dir_items = list(env_dir.iterdir())
    return EnvInfo(env=runtime_env, file_exists=envfile_exists, dir_list=dir_items, file_path=str(DEFAULT_ENV_FILE))


@router.get("/", response_model=List[ChatSessionSummary])
def list_chat_sessions(db: Session = Depends(get_session)):
    statement = select(
        ChatSession.id, 
        ChatSession.label, 
        ChatSession.created_at, 
        ChatSession.updated_at).order_by(ChatSession.updated_at.desc())
    sessions = db.exec(statement).all()
    return sessions


# --------- GET Session by ID ---------
@router.get("/{session_id}", response_model=ChatSession)
def get_session_by_id(session_id: UUID, session: Session = Depends(get_session)):
    chat = session.get(ChatSession, session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat


# --------- POST Create Session ---------
@router.post("/", response_model=ChatSession)
def create_session(label: str, db: Session = Depends(get_session)):
    chat = ChatSession(label=label)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


# --------- POST Append Message ---------
@router.post("/{session_id}/message", response_model=ChatSession)
def append_message(session_id: UUID, role: ChatRole, content: str, db: Session = Depends(get_session)):
    chat = db.get(ChatSession, session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Session not found")

    message = ChatMessage(
        role=role, 
        content=content, 
        timestamp=datetime.now(tz=timezone.utc).isoformat()
        )
    chat.messages.append(message.model_dump())
    chat.updated_at = datetime.now(timezone.utc)
    chat_data = chat.model_dump(exclude_unset=True)
    chat.sqlmodel_update(chat_data)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat
    


# --------- PATCH Rename Session ---------
@router.patch("/{session_id}", response_model=ChatSession)
def rename_session(session_id: UUID, label: str, db: Session = Depends(get_session)):
    chat = db.get(ChatSession, session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Session not found")

    chat.label = label
    chat.updated_at = datetime.now(timezone.utc)

    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_session)):
    session_id = payload.session_id
    query = payload.query

    chat = db.get(ChatSession, session_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Session not found")
    
    msg_history = [ChatMessage.model_validate(msg) for msg in chat.messages]
    msg_history_llm = [msg.to_llm_format() for msg in msg_history]

    # Add user's message
    user_msg = ChatMessage(
        role=ChatRole.USER, 
        content=query, 
        timestamp=datetime.now(tz=timezone.utc).isoformat()
    )
    
    chat.messages.append(user_msg.model_dump())

    # Simulate assistant response (replace this with your LLM logic)
    answer = orchrastrator_agent(query, msg_history_llm)
    
    assistant_msg = ChatMessage(
        role=ChatRole.ASSISTANT, 
        content=answer, 
        timestamp=datetime.now(tz=timezone.utc).isoformat()
        )
    chat.messages.append(assistant_msg.model_dump())

    # Update timestamps and commit
    chat.updated_at = datetime.now(tz=timezone.utc)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return ChatResponse(
        response=answer,
        success=True,
        # sources=sources
    )


# --------- DELETE Session ---------
@router.delete("/{session_id}")
def delete_session(session_id: UUID, db: Session = Depends(get_session)):
    chat = db.get(ChatSession, session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(chat)
    db.commit()
    return {"success": True}

