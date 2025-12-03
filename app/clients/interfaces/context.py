from abc import ABC, abstractmethod
from typing import List, Optional, Any
from uuid import UUID

from app.schemas.context import ContextResult, UnsummarizedMessages


class IContextManager(ABC):
    """Interface for LLM context management."""

    @abstractmethod
    def extract_unsummarized(
        self,
        all_messages: List[Any],
        summary_up_to_id: Optional[UUID],
    ) -> UnsummarizedMessages:
        """Extract messages not yet included in session summary."""
        pass

    @abstractmethod
    async def build_context(
        self,
        unsummarized: UnsummarizedMessages,
        new_message: str,
        current_summary: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> ContextResult:
        """Build context for LLM within token budget."""
        pass
