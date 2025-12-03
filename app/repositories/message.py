import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.message import Message
from app.repositories.interfaces.message import IMessageRepository
from app.core.enums import MessageRoleTypes
from app.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class MessageRepository(IMessageRepository):
    """Repository for message CRUD operations."""

    # region CREATE

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
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                sources=sources,
                tool_calls=tool_calls,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
            db.add(message)
            await db.flush()
            await db.refresh(message)

            return message

        except Exception as e:
            raise RepositoryError(f"Failed to create message: {e}") from e

    # endregion CREATE

    # region READ

    async def get_by_id(
        self,
        db: AsyncSession,
        message_id: UUID,
    ) -> Optional[Message]:
        """Get a message by ID."""
        try:
            result = await db.execute(select(Message).where(Message.id == message_id))
            return result.scalar_one_or_none()

        except Exception as e:
            raise RepositoryError(f"Failed to get message: {e}") from e

    async def get_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """Get messages for a session ordered by creation time, oldest first."""
        try:
            query = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())

            if limit is not None:
                query = query.limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get messages: {e}") from e

    async def count_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> int:
        """Count messages in a session."""
        try:
            result = await db.execute(select(func.count(Message.id)).where(Message.session_id == session_id))
            return result.scalar_one()

        except Exception as e:
            raise RepositoryError(f"Failed to count messages: {e}") from e

    # endregion READ

    # region DELETE

    async def delete_by_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> int:
        """Delete all messages in a session. Returns count of deleted messages."""
        try:
            result = await db.execute(delete(Message).where(Message.session_id == session_id))
            count = result.rowcount
            return count

        except Exception as e:
            raise RepositoryError(f"Failed to delete messages: {e}") from e

    # endregion DELETE
