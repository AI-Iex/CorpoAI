from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.schemas.user import User
from app.schemas.session import SessionResponse, SessionInfo, SessionCreate, SessionUpdate


class ISessionService(ABC):
    """Interface for session service operations."""

    @abstractmethod
    async def create(self, payload: SessionCreate) -> SessionResponse:
        """Create a new session."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: UUID, user: Optional[User]) -> SessionInfo:
        """Get a session by ID with message count."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user: Optional[User],
        skip: int = 0,
        limit: int = 50,
        read_anonymous: bool = False,
    ) -> tuple[List[SessionInfo], int]:
        """Get sessions for a user with pagination. Returns sessions and total_count."""
        pass

    @abstractmethod
    async def update(self, session_id: UUID, user: Optional[User], payload: SessionUpdate) -> SessionResponse:
        """Update a session."""
        pass

    @abstractmethod
    async def delete(self, session_id: UUID, user: Optional[User]) -> bool:
        """Delete a session."""
        pass
