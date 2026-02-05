"""
Message and Artifact schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    conversation_id: Optional[str] = None  # If None, create new conversation
    content: str = Field(..., min_length=1)
    role: Literal["user", "assistant"] = "user"


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    artifacts: List["ArtifactResponse"] = []

    class Config:
        from_attributes = True


class MessageSendResponse(BaseModel):
    """Response after sending a message (for optimistic UI)"""
    message_id: str
    conversation_id: str
    last_message_preview: str
    is_new_conversation: bool = False
    conversation_title: Optional[str] = None


class MessagesPageResponse(BaseModel):
    """Paginated messages response"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ArtifactCreate(BaseModel):
    """Schema for creating an artifact"""
    message_id: str
    conversation_id: str
    type: Literal["chart", "table", "code"]
    chart_type: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None
    data_snapshot: Optional[Any] = None


class ArtifactResponse(BaseModel):
    """Schema for artifact response"""
    id: str
    message_id: str
    type: str
    chart_type: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None
    data_snapshot: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Rebuild model to resolve forward references
MessageResponse.model_rebuild()
