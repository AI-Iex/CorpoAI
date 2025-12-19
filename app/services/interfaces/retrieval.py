from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID


class IRetrievalService(ABC):
    """Interface for retrieval service operations (RAG)."""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = None,
        min_score: float = None,
        document_ids: Optional[List[UUID]] = None,
        filter_enabled: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        """
        pass

    @abstractmethod
    async def get_context(
        self,
        query: str,
        max_tokens: int = 2000,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Get formatted context for LLM prompt.
        """
        pass

    @abstractmethod
    async def get_context_for_prompt(
        self,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Get context string ready to insert into prompt.
        """
        pass
