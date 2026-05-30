from __future__ import annotations

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./j_support_ai.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), default="New Conversation", nullable=False)
    language: Mapped[str] = mapped_column(String(12), default="ur-PK", nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
