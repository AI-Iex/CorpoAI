from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import UploadFile

from app.core.enums import DocumentStatus
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentList,
    DocumentStats,
)


class IDocumentService(ABC):
    """Interface for document service operations."""

    # region UPLOAD

    @abstractmethod
    async def upload(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        collection: str = "documents",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponse:
        """
        Upload and validate a document.
        """
        pass

    # endregion UPLOAD

    # region PROCESSING

    @abstractmethod
    async def process_document(
        self,
        document_id: UUID,
    ) -> DocumentResponse:
        """
        Process an uploaded document: extract text, chunk, embed, store.
        """
        pass

    # endregion PROCESSING

    # region READ

    @abstractmethod
    async def get_document(
        self,
        document_id: UUID,
    ) -> DocumentResponse:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def get_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[str] = None,
    ) -> DocumentList:
        """
        Get documents with pagination.
        """
        pass

    @abstractmethod
    async def get_stats(self) -> DocumentStats:
        """Get document statistics."""
        pass

    # endregion READ

    # region DELETE

    @abstractmethod
    async def delete_document(
        self,
        document_id: UUID,
    ) -> bool:
        """
        Delete a document and its chunks from vector store.
        """
        pass

    # endregion DELETE
