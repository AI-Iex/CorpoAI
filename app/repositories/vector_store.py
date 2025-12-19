import logging
from typing import List, Optional, Dict, Any
from chromadb import Collection
from app.db.chroma_client import get_or_create_collection
from app.repositories.interfaces.vector_store import IVectorStoreRepository

logger = logging.getLogger(__name__)


class VectorStoreRepository(IVectorStoreRepository):
    """
    Repository for vector store CRUD operations with ChromaDB.
    """

    def __init__(self, collection_name: str = "documents"):
        self._collection_name = collection_name
        self._collection: Optional[Collection] = None

    def _get_collection(self) -> Collection:
        """
        Lazy load the collection.
        """

        if self._collection is None:
            self._collection = get_or_create_collection(
                collection_name=self._collection_name,
                metadata={
                    "description": f"Document chunks for RAG - {self._collection_name}",
                    "hnsw:space": "cosine",
                },
            )
        return self._collection

    # region CRUD Operations

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
        if not ids:
            return 0

        collection = self._get_collection()

        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.debug(f"Added {len(ids)} items to collection")
            return len(ids)

        except Exception as e:
            logger.error(f"Failed to add items: {e}")
            raise

    async def query(
        self,
        query_embedding: List[float],
        n_results: int,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the collection by embedding.
        """
        collection = self._get_collection()

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            logger.debug(f"Query returned {len(results.get('ids', [[]])[0])} results")
            return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def get(
        self,
        where: Dict[str, Any],
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get documents by filter.
        """

        collection = self._get_collection()
        include = include or ["documents", "metadatas"]

        try:
            results = collection.get(
                where=where,
                include=include,
            )
            return results

        except Exception as e:
            logger.error(f"Get failed: {e}")
            raise

    async def delete(
        self,
        where: Dict[str, Any],
    ) -> int:
        """
        Delete documents by filter.
        """

        collection = self._get_collection()

        try:
            # Get count before deletion
            existing = await self.get(where=where, include=[])
            count = len(existing["ids"]) if existing["ids"] else 0

            if count > 0:
                collection.delete(where=where)
                logger.debug(f"Deleted {count} items")

            return count

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    async def count(
        self,
        where: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count documents in collection.
        """

        collection = self._get_collection()

        try:
            if where:
                results = await self.get(where=where, include=[])
                return len(results["ids"]) if results["ids"] else 0
            return collection.count()

        except Exception as e:
            logger.error(f"Count failed: {e}")
            raise

    # endregion CRUD Operations

    @property
    def collection_name(self) -> str:
        return self._collection_name
