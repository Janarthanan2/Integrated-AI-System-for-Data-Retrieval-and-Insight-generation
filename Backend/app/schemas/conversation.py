"""
Conversation schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation"""
    title: Optional[str] = Field(None, max_length=255)
    first_message: Optional[str] = None  # Auto-generate title from this


class ConversationUpdate(BaseModel):
    """Schema for updating conversation"""
    title: str = Field(..., min_length=1, max_length=255)


class ConversationSidebarItem(BaseModel):
    """Lightweight schema for sidebar list"""
    id: str
    title: str
    last_message: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Full conversation response"""
    id: str
    title: str
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages (for loading a chat)"""
    messages: List["MessageResponse"] = []


class SidebarResponse(BaseModel):
    """Response for sidebar API"""
    conversations: List[ConversationSidebarItem]
    total: int


# Import here to avoid circular imports
from .message import MessageResponse
ConversationWithMessages.model_rebuild()
