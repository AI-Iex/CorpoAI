import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.document import Document
from app.repositories.interfaces.document import IDocumentRepository
from app.core.enums import DocumentStatus, DocumentTypeFile
from app.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class DocumentRepository(IDocumentRepository):
    """Repository for document CRUD operations."""

    # region CREATE

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
        try:
            document = Document(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                file_type=file_type.value,
                file_size=file_size,
                status=DocumentStatus.PENDING,
                chroma_collection=chroma_collection,
                metadata_=metadata or {},
            )
            db.add(document)
            await db.flush()
            await db.refresh(document)

            return document

        except IntegrityError as e:
            raise RepositoryError("Failed to create document: integrity error") from e

        except Exception as e:
            raise RepositoryError(f"Failed to create document: {e}") from e

    # endregion CREATE

    # region READ

    async def get_by_id(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> Optional[Document]:
        """Get a document by ID."""
        try:
            query = select(Document).where(Document.id == document_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            raise RepositoryError(f"Failed to get document: {e}") from e

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[DocumentTypeFile] = None,
    ) -> List[Document]:
        """Get all documents with optional filters."""
        try:
            query = select(Document)

            if status:
                query = query.where(Document.status == status)
            if file_type:
                query = query.where(Document.file_type == file_type.value)

            query = query.order_by(Document.created_at.desc())
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get documents: {e}") from e

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Document]:
        """Get documents uploaded by a specific user."""
        try:
            query = (
                select(Document)
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get user documents: {e}") from e

    async def count(
        self,
        db: AsyncSession,
        status: Optional[DocumentStatus] = None,
    ) -> int:
        """Count documents with optional status filter."""
        try:
            query = select(func.count(Document.id))
            if status:
                query = query.where(Document.status == status)

            result = await db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            raise RepositoryError(f"Failed to count documents: {e}") from e

    async def get_enabled_ids(
        self,
        db: AsyncSession,
    ) -> List[UUID]:
        """Get IDs of all enabled documents for RAG."""
        try:
            query = select(Document.id).where(Document.is_enabled).where(Document.status == DocumentStatus.COMPLETED)
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get enabled document IDs: {e}") from e

    # endregion READ

    # region UPDATE

    async def update_status(
        self,
        db: AsyncSession,
        document_id: UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None,
        num_chunks: Optional[int] = None,
    ) -> Optional[Document]:
        """Update document processing status."""
        try:
            # Build update values
            values = {"status": status}
            if error_message is not None:
                values["error_message"] = error_message
            if num_chunks is not None:
                values["num_chunks"] = num_chunks

            # Execute update
            stmt = update(Document).where(Document.id == document_id).values(**values)
            await db.execute(stmt)
            await db.flush()

            # Return updated document
            return await self.get_by_id(db, document_id)

        except Exception as e:
            raise RepositoryError(f"Failed to update document status: {e}") from e

    async def update_metadata(
        self,
        db: AsyncSession,
        document_id: UUID,
        metadata: Dict[str, Any],
    ) -> Optional[Document]:
        """Update document metadata (merges with existing)."""
        try:
            # Get current document
            document = await self.get_by_id(db, document_id)
            if not document:
                return None

            # Merge metadata
            current_metadata = document.metadata_ or {}
            current_metadata.update(metadata)

            # Update
            stmt = update(Document).where(Document.id == document_id).values(metadata_=current_metadata)
            await db.execute(stmt)
            await db.flush()

            return await self.get_by_id(db, document_id)

        except Exception as e:
            raise RepositoryError(f"Failed to update document metadata: {e}") from e

    async def update_enabled(
        self,
        db: AsyncSession,
        document_id: UUID,
        is_enabled: bool,
    ) -> Optional[Document]:
        """Update document enabled status for RAG."""
        try:
            stmt = update(Document).where(Document.id == document_id).values(is_enabled=is_enabled)
            result = await db.execute(stmt)
            await db.flush()

            if result.rowcount == 0:
                return None

            updated_doc = await self.get_by_id(db, document_id)
            return updated_doc

        except Exception as e:
            raise RepositoryError(f"Failed to update document enabled status: {e}") from e

    # endregion UPDATE

    # region DELETE

    async def delete(
        self,
        db: AsyncSession,
        document_id: UUID,
    ) -> bool:
        """Delete a document by ID."""
        try:
            stmt = delete(Document).where(Document.id == document_id)
            result = await db.execute(stmt)
            await db.flush()

            deleted = result.rowcount > 0
            return deleted

        except Exception as e:
            raise RepositoryError(f"Failed to delete document: {e}") from e

    # endregion DELETE

    # region STATS

    async def get_stats(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Get document statistics."""
        try:
            # Total count
            total_count = await self.count(db)

            # Count by status
            status_counts = {}
            for status in DocumentStatus:
                count = await self.count(db, status=status)
                status_counts[status.value] = count

            # Count by file type
            type_query = select(
                Document.file_type,
                func.count(Document.id).label("count"),
            ).group_by(Document.file_type)
            type_result = await db.execute(type_query)
            type_counts = {row[0]: row[1] for row in type_result.all()}

            # Total size
            size_query = select(func.sum(Document.file_size))
            size_result = await db.execute(size_query)
            total_size = size_result.scalar() or 0

            # Total chunks
            chunks_query = select(func.sum(Document.num_chunks))
            chunks_result = await db.execute(chunks_query)
            total_chunks = chunks_result.scalar() or 0

            return {
                "total_documents": total_count,
                "total_chunks": total_chunks,
                "total_size_bytes": total_size,
                "by_status": status_counts,
                "by_type": type_counts,
            }

        except Exception as e:
            raise RepositoryError(f"Failed to get document stats: {e}") from e

    # endregion STATS
