from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.core.enums import DocumentStatus, DocumentTypeFile


class IDocumentRepository(ABC):
    """Interface for document repository operations."""

    # region CREATE

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        filename: str,
        file_path: str,
        file_type: DocumentTypeFile,
        file_size: int,
        chroma_collection: str = "documents",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Create a new document record."""
        pass

    # endregion CREATE

    # region READ

    @abstractmethod
    async def get_by_id(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> Optional[Document]:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[DocumentTypeFile] = None,
    ) -> List[Document]:
        """Get all documents with optional filters."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Document]:
        """Get documents uploaded by a specific user."""
        pass

    @abstractmethod
    async def count(
        self,
        db: AsyncSession,
        status: Optional[DocumentStatus] = None,
    ) -> int:
        """Count documents with optional status filter."""
        pass

    @abstractmethod
    async def get_enabled_ids(
        self,
        db: AsyncSession,
    ) -> List[UUID]:
        """Get IDs of all enabled documents for RAG."""
        pass

    # endregion READ

    # region UPDATE

    @abstractmethod
    async def update_status(
        self,
        db: AsyncSession,
        document_id: UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None,
        num_chunks: Optional[int] = None,
    ) -> Optional[Document]:
        """Update document processing status."""
        pass

    @abstractmethod
    async def update_metadata(
        self,
        db: AsyncSession,
        document_id: UUID,
        metadata: Dict[str, Any],
    ) -> Optional[Document]:
        """Update document metadata."""
        pass

    @abstractmethod
    async def update_enabled(
        self,
        db: AsyncSession,
        document_id: UUID,
        is_enabled: bool,
    ) -> Optional[Document]:
        """Update document enabled status for RAG."""
        pass

    # endregion UPDATE

    # region DELETE

    @abstractmethod
    async def delete(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> bool:
        """Delete a document by ID."""
        pass

    # endregion DELETE

    # region STATS

    @abstractmethod
    async def get_stats(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Get document statistics."""
        pass

    # endregion STATS
