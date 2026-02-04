"""
Conversation API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models.base import get_db
from ..schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    SidebarResponse
)
from ..schemas.message import (
    MessageCreate,
    MessageSendResponse,
    MessagesPageResponse,
    ArtifactCreate,
    ArtifactResponse
)
from ..services.conversation_service import ConversationService
from .auth import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


# ==================== SIDEBAR ====================

@router.get("/sidebar", response_model=SidebarResponse)
async def get_sidebar(
    limit: int = Query(50, le=100),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation sidebar for current user.
    
    Returns lightweight list for fast sidebar loading.
    Results are cached for 30 seconds.
    """
    return await ConversationService.get_sidebar(
        db, 
        user_id=current_user.id,
        limit=limit
    )


# ==================== CONVERSATIONS ====================

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation.
    
    - **title**: Optional title (auto-generated from first message if not provided)
    - **first_message**: Optional first message content (used to generate title)
    """
    return await ConversationService.create_conversation(
        db,
        user_id=current_user.id,
        data=data
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific conversation.
    
    Only returns if conversation belongs to current user.
    """
    conversation = await ConversationService.get_conversation(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    return ConversationResponse.model_validate(conversation)


@router.put("/{conversation_id}/title", response_model=ConversationResponse)
async def update_title(
    conversation_id: str,
    data: ConversationUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update conversation title.
    """
    return await ConversationService.update_title(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        new_title=data.title
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    """
    await ConversationService.delete_conversation(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    return None


# ==================== MESSAGES ====================

@router.get("/{conversation_id}/messages", response_model=MessagesPageResponse)
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated messages for a conversation.
    
    - **page**: Page number (1-indexed)
    - **page_size**: Messages per page (max 100)
    
    Messages are ordered by creation time (oldest first).
    """
    return await ConversationService.get_messages(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size
    )


@router.post("/messages", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a conversation.
    
    - If **conversation_id** is null, creates a new conversation.
    - Returns message_id and updated conversation info for optimistic UI.
    
    Note: This only stores the message. Use /query endpoint for AI responses.
    """
    return await ConversationService.add_message(
        db,
        user_id=current_user.id,
        data=data
    )


# ==================== ARTIFACTS ====================

@router.get("/{conversation_id}/artifacts", response_model=list[ArtifactResponse])
async def get_artifacts(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all artifacts (charts, tables) for a conversation.
    """
    return await ConversationService.get_artifacts(
        db,
        user_id=current_user.id,
        conversation_id=conversation_id
    )


@router.post("/artifacts", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    data: ArtifactCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an artifact (chart, table, code) for a message.
    
    This is typically called internally after AI generates a chart.
    """
    return await ConversationService.add_artifact(
        db,
        user_id=current_user.id,
        data=data
    )
