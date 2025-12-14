from abc import ABC, abstractmethod
from typing import List
from app.schemas.embedding import EmbeddingBatchResult, QueryEmbeddingResult


class IEmbeddingClient(ABC):
    """Interface for embedding clients."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name being used.
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Get the embedding dimension.
        """
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> EmbeddingBatchResult:
        """
        Generate embeddings for documents (for storage).
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> QueryEmbeddingResult:
        """
        Generate embedding for a search query.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if embedding service is healthy and model is loaded.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Cleanup resources.
        """
        pass
