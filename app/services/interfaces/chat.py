from abc import ABC, abstractmethod
from typing import Optional, List, AsyncIterator
from uuid import UUID
from app.schemas.user import User
from app.schemas.message import (
    MessageCreate,
    ChatResponse,
    SessionHistory,
    UserMessageResponse,
    AssistantMessageResponse,
)
from app.schemas.streaming import StreamChunk


class IChatService(ABC):
    """Interface for chat service operations."""

    @abstractmethod
    async def send_message(self, payload: MessageCreate) -> ChatResponse:
        """
        Send a message and get AI response.
        Creates a new session if session_id is not provided.
        """
        pass

    @abstractmethod
    async def send_message_stream(self, payload: MessageCreate) -> AsyncIterator[StreamChunk]:
        """
        Send a message and stream the AI response.
        Creates a new session if session_id is not provided.
        """
        pass

    @abstractmethod
    async def get_session_history(
        self,
        session_id: UUID,
        user: User = None,
        limit: Optional[int] = None,
    ) -> SessionHistory:
        """Get message history for a session."""
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[UserMessageResponse | AssistantMessageResponse]:
        """Get messages for a session."""
        pass
