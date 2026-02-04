"""
Conversation service for managing chat history
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..db_models.conversation import Conversation, Message, Artifact
from ..schemas.conversation import (
    ConversationCreate, 
    ConversationSidebarItem,
    ConversationResponse,
    SidebarResponse
)
from ..schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageSendResponse,
    MessagesPageResponse,
    ArtifactCreate,
    ArtifactResponse
)


# In-memory cache for sidebar (simple implementation)
# In production, use Redis
_sidebar_cache: Dict[str, tuple[List[ConversationSidebarItem], datetime]] = {}
CACHE_TTL_SECONDS = 30


class ConversationService:
    """Service for managing conversations and messages"""

    @staticmethod
    def _invalidate_cache(user_id: str):
        """Invalidate sidebar cache for user"""
        if user_id in _sidebar_cache:
            del _sidebar_cache[user_id]

    @staticmethod
    def _generate_title(content: str, max_length: int = 50) -> str:
        """Generate a title from the first message content"""
        # Clean and truncate
        title = content.strip()
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."
        return title or "New Chat"

    @staticmethod
    async def get_sidebar(
        db: AsyncSession, 
        user_id: str, 
        limit: int = 50,
        use_cache: bool = True
    ) -> SidebarResponse:
        """Get sidebar items for user (cached)"""
        
        # Check cache
        if use_cache and user_id in _sidebar_cache:
            cached, timestamp = _sidebar_cache[user_id]
            if (datetime.utcnow() - timestamp).seconds < CACHE_TTL_SECONDS:
                return SidebarResponse(conversations=cached, total=len(cached))
        
        # Query database
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        # Convert to schema
        items = [
            ConversationSidebarItem.model_validate(conv) 
            for conv in conversations
        ]
        
        # Cache result
        _sidebar_cache[user_id] = (items, datetime.utcnow())
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
        )
        total = count_result.scalar() or 0
        
        return SidebarResponse(conversations=items, total=total)

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: str,
        data: ConversationCreate
    ) -> ConversationResponse:
        """Create a new conversation"""
        title = data.title or "New Chat"
        
        # If first_message provided, generate title from it
        if data.first_message:
            title = ConversationService._generate_title(data.first_message)
        
        conversation = Conversation(
            user_id=user_id,
            title=title
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        # Invalidate cache
        ConversationService._invalidate_cache(user_id)
        
        return ConversationResponse.model_validate(conversation)

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        user_id: str,
        conversation_id: str
    ) -> Conversation:
        """Get a conversation by ID (with user validation)"""
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id  # User isolation!
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation

    @staticmethod
    async def update_title(
        db: AsyncSession,
        user_id: str,
        conversation_id: str,
        new_title: str
    ) -> ConversationResponse:
        """Update conversation title"""
        conversation = await ConversationService.get_conversation(
            db, user_id, conversation_id
        )
        
        conversation.title = new_title
        await db.commit()
        await db.refresh(conversation)
        
        # Invalidate cache
        ConversationService._invalidate_cache(user_id)
        
        return ConversationResponse.model_validate(conversation)

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        user_id: str,
        conversation_id: str
    ) -> bool:
        """Delete a conversation"""
        conversation = await ConversationService.get_conversation(
            db, user_id, conversation_id
        )
        
        await db.delete(conversation)
        await db.commit()
        
        # Invalidate cache
        ConversationService._invalidate_cache(user_id)
        
        return True

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        user_id: str,
        conversation_id: str,
        page: int = 1,
        page_size: int = 30
    ) -> MessagesPageResponse:
        """Get paginated messages for a conversation"""
        # Validate conversation belongs to user
        await ConversationService.get_conversation(db, user_id, conversation_id)
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        total = count_result.scalar() or 0
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get messages with artifacts
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .options(selectinload(Message.artifacts))
            .order_by(Message.created_at)
            .offset(offset)
            .limit(page_size)
        )
        messages = result.scalars().all()
        
        # Convert to schema
        message_responses = []
        for msg in messages:
            msg_dict = MessageResponse.model_validate(msg)
            message_responses.append(msg_dict)
        
        return MessagesPageResponse(
            messages=message_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total
        )

    @staticmethod
    async def add_message(
        db: AsyncSession,
        user_id: str,
        data: MessageCreate
    ) -> MessageSendResponse:
        """Add a message to a conversation"""
        is_new_conversation = False
        conversation_title = None
        
        # Check if we need to create a new conversation
        if not data.conversation_id:
            # Create new conversation with title from first message
            conversation = Conversation(
                user_id=user_id,
                title=ConversationService._generate_title(data.content),
                last_message=data.content[:100] if data.role == "user" else None
            )
            db.add(conversation)
            await db.flush()  # Get the ID
            is_new_conversation = True
            conversation_title = conversation.title
        else:
            # Get existing conversation
            conversation = await ConversationService.get_conversation(
                db, user_id, data.conversation_id
            )
        
        # Create message
        message = Message(
            conversation_id=conversation.id,
            role=data.role,
            content=data.content
        )
        db.add(message)
        
        # Update conversation metadata
        if data.role == "user":
            conversation.last_message = data.content[:100]
        
        await db.commit()
        await db.refresh(message)
        
        # Invalidate cache
        ConversationService._invalidate_cache(user_id)
        
        return MessageSendResponse(
            message_id=message.id,
            conversation_id=conversation.id,
            last_message_preview=conversation.last_message or "",
            is_new_conversation=is_new_conversation,
            conversation_title=conversation_title
        )

    @staticmethod
    async def add_artifact(
        db: AsyncSession,
        user_id: str,
        data: ArtifactCreate
    ) -> ArtifactResponse:
        """Add an artifact to a message"""
        # Validate conversation belongs to user
        await ConversationService.get_conversation(db, user_id, data.conversation_id)
        
        artifact = Artifact(
            message_id=data.message_id,
            conversation_id=data.conversation_id,
            type=data.type,
            chart_type=data.chart_type,
            spec=data.spec,
            data_snapshot=data.data_snapshot
        )
        
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        
        return ArtifactResponse.model_validate(artifact)

    @staticmethod
    async def get_artifacts(
        db: AsyncSession,
        user_id: str,
        conversation_id: str
    ) -> List[ArtifactResponse]:
        """Get all artifacts for a conversation"""
        # Validate conversation belongs to user
        await ConversationService.get_conversation(db, user_id, conversation_id)
        
        result = await db.execute(
            select(Artifact)
            .where(Artifact.conversation_id == conversation_id)
            .order_by(Artifact.created_at)
        )
        artifacts = result.scalars().all()
        
        return [ArtifactResponse.model_validate(a) for a in artifacts]
