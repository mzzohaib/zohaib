from __future__ import annotations

from typing import List

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from database import ChatMessage, ChatSession


ALLOWED_ROLES = {"system", "user", "assistant"}


def get_or_create_session(db: Session, session_id: str) -> ChatSession:
    session_obj = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
    if session_obj:
        return session_obj

    session_obj = ChatSession(session_id=session_id)
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj


def add_message(db: Session, *, session_id: str, message_id: str, role: str, content: str) -> ChatMessage:
    if role not in ALLOWED_ROLES:
        raise ValueError("Unsupported role")

    _ = get_or_create_session(db, session_id)
    msg = ChatMessage(message_id=message_id, session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_recent_messages(db: Session, session_id: str, exchanges: int = 6) -> List[dict]:
    limit_messages = exchanges * 2

    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at), desc(ChatMessage.id))
            .limit(limit_messages)
        )
        .scalars()
        .all()
    )

    ordered = sorted(rows, key=lambda m: (m.created_at, m.id))
    return [{"role": item.role, "content": item.content} for item in ordered]


def get_sessions(db: Session, limit: int = 50) -> List[dict]:
    sessions = (
        db.execute(select(ChatSession).order_by(desc(ChatSession.updated_at), asc(ChatSession.id)).limit(limit))
        .scalars()
        .all()
    )
    return [
        {
            "session_id": s.session_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


def get_session_messages(db: Session, session_id: str, limit: int = 100) -> List[dict]:
    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(asc(ChatMessage.created_at), asc(ChatMessage.id))
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "message_id": m.message_id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in rows
    ]
