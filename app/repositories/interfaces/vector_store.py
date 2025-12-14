from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IVectorStoreRepository(ABC):
    """
    Interface for vector store CRUD operations.
    """

    @abstractmethod
    async def add(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """
        Add documents with embeddings to the collection.
        """
        pass

    @abstractmethod
    async def query(
        self,
        query_embedding: List[float],
        n_results: int,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the collection by embedding.
        """
        pass

    @abstractmethod
    async def get(
        self,
        where: Dict[str, Any],
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get documents by filter.
        """
        pass

    @abstractmethod
    async def delete(
        self,
        where: Dict[str, Any],
    ) -> int:
        """
        Delete documents.
        """
        pass

    @abstractmethod
    async def count(
        self,
        where: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count documents in collection.
        """
        pass

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Get the collection name."""
        pass
