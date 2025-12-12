from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session as SessionModel


class ISessionRepository(ABC):
    """Interface for session repository operations."""

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        title: str,
    ) -> SessionModel:
        """Create a new session."""
        pass

    @abstractmethod
    async def get_by_id(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> Optional[SessionModel]:
        """Get a session by ID."""
        pass

    @abstractmethod
    async def get_by_id_and_user(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[SessionModel]:
        """Get a session by ID for a specific user."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        skip: int = 0,
        limit: int = 50,
    ) -> List[SessionModel]:
        """Get sessions for a user with pagination."""
        pass

    @abstractmethod
    async def get_by_superuser(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SessionModel]:
        """Get sessions for a superuser with pagination, including both own and anonymous sessions."""
        pass

    @abstractmethod
    async def count_by_user(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
    ) -> int:
        """Count total sessions for a user."""
        pass

    @abstractmethod
    async def update_title(
        self,
        db: AsyncSession,
        session_id: UUID,
        title: str,
    ) -> Optional[SessionModel]:
        """Update session title."""
        pass

    @abstractmethod
    async def update_summary(
        self,
        db: AsyncSession,
        session_id: UUID,
        summary: str,
        summary_up_to_message_id: UUID,
    ) -> Optional[SessionModel]:
        """Update session summary and the last summarized message ID."""
        pass

    @abstractmethod
    async def delete(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> bool:
        """Delete a session by ID."""
        pass
