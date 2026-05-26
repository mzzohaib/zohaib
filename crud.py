from __future__ import annotations

from typing import List

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.orm import Session

from database import ChatMessage, ChatSession, MessageFeedback

ALLOWED_ROLES = {"system", "user", "assistant"}


def get_or_create_session(db: Session, session_id: str, language: str = "ur-PK") -> ChatSession:
    session_obj = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
    if session_obj:
        return session_obj
    session_obj = ChatSession(session_id=session_id, language=language)
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj


def update_session_meta(db: Session, session_id: str, *, title: str | None = None, pinned: bool | None = None, archived: bool | None = None) -> ChatSession:
    obj = get_or_create_session(db, session_id)
    if title is not None:
        obj.title = title
    if pinned is not None:
        obj.pinned = pinned
    if archived is not None:
        obj.archived = archived
    db.commit()
    db.refresh(obj)
    return obj


def add_message(db: Session, *, session_id: str, message_id: str, role: str, content: str, edited: bool = False, parent_message_id: str | None = None, sentiment: str = "neutral") -> ChatMessage:
    if role not in ALLOWED_ROLES:
        raise ValueError("Unsupported role")
    _ = get_or_create_session(db, session_id)
    msg = ChatMessage(message_id=message_id, session_id=session_id, role=role, content=content, edited=edited, parent_message_id=parent_message_id, sentiment=sentiment)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def edit_message(db: Session, session_id: str, message_id: str, new_content: str) -> ChatMessage | None:
    msg = db.scalar(select(ChatMessage).where(ChatMessage.session_id == session_id, ChatMessage.message_id == message_id))
    if not msg:
        return None
    msg.content = new_content
    msg.edited = True
    db.commit()
    db.refresh(msg)
    return msg


def delete_message(db: Session, session_id: str, message_id: str) -> bool:
    msg = db.scalar(select(ChatMessage).where(ChatMessage.session_id == session_id, ChatMessage.message_id == message_id))
    if not msg:
        return False
    db.delete(msg)
    db.commit()
    return True


def get_recent_messages(db: Session, session_id: str, exchanges: int = 6) -> List[dict]:
    rows = db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(desc(ChatMessage.created_at), desc(ChatMessage.id)).limit(exchanges * 2)).scalars().all()
    ordered = sorted(rows, key=lambda m: (m.created_at, m.id))
    return [{"role": item.role, "content": item.content} for item in ordered]


def get_sessions(db: Session, limit: int = 100, query: str | None = None) -> List[dict]:
    stmt = select(ChatSession)
    if query:
        stmt = stmt.where(ChatSession.title.ilike(f"%{query}%"))
    sessions = db.execute(stmt.order_by(desc(ChatSession.pinned), desc(ChatSession.updated_at)).limit(limit)).scalars().all()
    return [{"session_id": s.session_id, "title": s.title, "language": s.language, "pinned": s.pinned, "archived": s.archived, "created_at": s.created_at.isoformat() if s.created_at else None, "updated_at": s.updated_at.isoformat() if s.updated_at else None} for s in sessions]


def get_session_messages(db: Session, session_id: str, limit: int = 200) -> List[dict]:
    rows = db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(asc(ChatMessage.created_at), asc(ChatMessage.id)).limit(limit)).scalars().all()
    return [{"message_id": m.message_id, "role": m.role, "content": m.content, "edited": m.edited, "parent_message_id": m.parent_message_id, "sentiment": m.sentiment, "created_at": m.created_at.isoformat() if m.created_at else None} for m in rows]


def search_messages(db: Session, term: str, limit: int = 100) -> List[dict]:
    rows = db.execute(select(ChatMessage).where(or_(ChatMessage.content.ilike(f"%{term}%"), ChatMessage.sentiment.ilike(f"%{term}%"))).order_by(desc(ChatMessage.created_at)).limit(limit)).scalars().all()
    return [{"session_id": m.session_id, "message_id": m.message_id, "content": m.content, "role": m.role} for m in rows]


def add_feedback(db: Session, session_id: str, message_id: str, rating: int, comment: str = "") -> MessageFeedback:
    fb = MessageFeedback(session_id=session_id, message_id=message_id, rating=rating, comment=comment[:500])
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb
