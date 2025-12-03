from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.schemas.session import SessionResponse, SessionInfo, SessionCreate, SessionUpdate


class ISessionService(ABC):
    """Interface for session service operations."""

    @abstractmethod
    async def create(self, payload: SessionCreate) -> SessionResponse:
        """Create a new session."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> SessionResponse:
        """Get a session by ID."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: Optional[UUID],
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[SessionInfo], int]:
        """Get sessions for a user with pagination. Returns sessions and total_count."""
        pass

    @abstractmethod
    async def update(self, session_id: UUID, payload: SessionUpdate) -> SessionResponse:
        """Update a session."""
        pass

    @abstractmethod
    async def delete(self, session_id: UUID) -> bool:
        """Delete a session."""
        pass
