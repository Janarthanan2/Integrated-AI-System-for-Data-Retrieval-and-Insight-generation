"""
Conversation, Message, and Artifact models for chat history
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Conversation(Base):
    """Conversation/Chat session model"""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Chat")
    last_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    artifacts = relationship("Artifact", back_populates="conversation", cascade="all, delete-orphan")

    # Composite index for efficient sidebar queries
    __table_args__ = (
        Index("idx_user_updated", "user_id", "updated_at"),
    )

    def __repr__(self):
        return f"<Conversation {self.id[:8]}... '{self.title[:20]}...'>"


class Message(Base):
    """Individual message in a conversation"""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", name="message_role"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    artifacts = relationship("Artifact", back_populates="message", cascade="all, delete-orphan")

    # Index for pagination queries
    __table_args__ = (
        Index("idx_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self):
        return f"<Message {self.role}: {self.content[:30]}...>"


class Artifact(Base):
    """Stored artifacts like charts, tables, etc."""
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(
        Enum("chart", "table", "code", name="artifact_type"),
        nullable=False
    )
    chart_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    spec: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    data_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    message = relationship("Message", back_populates="artifacts")
    conversation = relationship("Conversation", back_populates="artifacts")

    def __repr__(self):
        return f"<Artifact {self.type}: {self.chart_type or 'N/A'}>"
