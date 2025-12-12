from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.core.enums import MessageRoleTypes


class IMessageRepository(ABC):
    """Interface for message repository operations."""

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        session_id: UUID,
        role: MessageRoleTypes,
        content: str,
        sources: Optional[List[dict]] = None,
        tool_calls: Optional[List[dict]] = None,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[float] = None,
    ) -> Message:
        """Create a new message."""
        pass

    @abstractmethod
    async def get_by_id(
        self,
        db: AsyncSession,
        message_id: UUID,
    ) -> Optional[Message]:
        """Get a message by ID."""
        pass

    @abstractmethod
    async def get_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """Get messages for a session ordered by creation time."""
        pass

    @abstractmethod
    async def count_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> int:
        """Count messages in a session."""
        pass

    @abstractmethod
    async def delete_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> int:
        """Delete all messages in a session. Returns count of deleted messages."""
        pass
