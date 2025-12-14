import logging
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import UploadFile
from app.core.config import settings
from app.core.enums import DocumentStatus
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentUploadError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentExtractionError,
    DocumentProcessingError,
)
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentList,
    DocumentStats,
)
from app.core.enums import DocumentTypeFile
from app.db.unit_of_work import UnitOfWorkFactory
from app.repositories.interfaces.document import IDocumentRepository
from app.repositories.interfaces.vector_store import IVectorStoreRepository
from app.services.interfaces.document import IDocumentService
from app.services.interfaces.chunking import IChunkingService
from app.services.interfaces.file_storage import IFileStorage
from app.clients.interfaces import IEmbeddingClient

logger = logging.getLogger(__name__)


class DocumentService(IDocumentService):
    """
    Service for document management and processing.
    """

    def __init__(
        self,
        document_repo: IDocumentRepository,
        vector_store: IVectorStoreRepository,
        chunking_service: IChunkingService,
        file_storage: IFileStorage,
        embedding_client: IEmbeddingClient,
        uow_factory: UnitOfWorkFactory,
    ):
        """
        Initialize document service.
        """
        self._document_repo = document_repo
        self._vector_store = vector_store
        self._chunking_service = chunking_service
        self._file_storage = file_storage
        self._embedding_client = embedding_client
        self._uow = uow_factory

        logger.debug("DocumentService initialized")

    # region VALIDATION

    def _validate_file(self, file_size: int, extension: str) -> None:
        """
        Validate file before upload.
        """
        # Check supported type
        if extension not in DocumentTypeFile._value2member_map_:
            raise UnsupportedFileTypeError(extension)

        # Check size
        max_size = settings.max_upload_size_bytes
        if file_size > max_size:
            raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)

    # endregion VALIDATION

    # region UPLOAD

    async def upload(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        collection: str = "documents",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponse:
        """
        Upload and validate a document (does not process yet).
        """

        logger.info(f"Trying to upload document: {file.filename}")

        # Get filename and extension
        filename = file.filename or "unnamed"
        extension = Path(filename).suffix.lower().lstrip(".")

        # Read file content
        content = await file.read()
        if content is None:
            raise DocumentProcessingError("Failed to read uploaded file")

        # Determine file size
        file_size = file.size if file.size is not None else len(content)

        # Validate
        self._validate_file(file_size, extension)

        # Save file using storage backend
        storage_path = await self._file_storage.save(filename, content)

        # Create document record in database
        async with self._uow() as db:

            document = await self._document_repo.create(
                db=db,
                user_id=user_id,
                filename=filename,
                file_path=storage_path,
                file_type=DocumentTypeFile(extension),
                file_size=file_size,
                chroma_collection=collection,
                metadata=metadata,
            )

            logger.info(f"Document uploaded: {document.id} ({filename})")

            return DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                status=document.status,
                message="Document uploaded successfully. Processing queued.",
            )

    # endregion UPLOAD

    # region PROCESSING

    async def process_document(
        self,
        document_id: UUID,
    ) -> DocumentResponse:
        """
        Process an uploaded document: extract text, chunk, embed, store.
        """
        async with self._uow() as db:

            # Get document
            document = await self._document_repo.get_by_id(db, document_id)
            if not document:
                logger.warning(f"Document not found: {document_id}, cannot process")
                raise DocumentNotFoundError(str(document_id))

            if document.status != DocumentStatus.PENDING:
                logger.warning(f"Document {document_id} already processed (status={document.status})")
                return DocumentResponse.model_validate(document)

            # Update status to processing
            await self._document_repo.update_status(db, document_id, DocumentStatus.PROCESSING)

            try:
                logger.info(f"Started processing document {document_id} : {document.filename}")

                # 1. Extract text and split into chunks
                logger.debug(f"Processing document {document_id}: extracting text")
                full_path = self._file_storage.get_full_path(document.file_path)
                chunks, doc_metadata = await self._chunking_service.process_file(full_path)

                if not chunks:
                    raise DocumentExtractionError("No text content extracted from document")

                # 2. Generate embeddings
                logger.debug(f"Processing document {document_id}: generating embeddings for {len(chunks)} chunks")
                chunk_texts = [c.text for c in chunks]
                embedding_result = await self._embedding_client.embed_documents(chunk_texts)

                # 3. Store in vector database
                logger.debug(f"Processing document {document_id}: storing in ChromaDB")

                # Build IDs and metadata (business logic in service)
                doc_id_str = str(document_id)
                ids = [f"{doc_id_str}_{i}" for i in range(len(chunks))]

                metadatas = []
                for i, chunk in enumerate(chunks):
                    # Start with chunk metadata, filtering out None values
                    chunk_meta = {k: v for k, v in chunk.metadata.model_dump().items() if v is not None}
                    # Add document-level metadata
                    meta = {
                        "document_id": doc_id_str,
                        "chunk_index": i,
                        "chunk_length": len(chunk.text),
                        "filename": document.filename,
                        "file_type": document.file_type,
                        **chunk_meta,
                    }
                    metadatas.append(meta)

                num_chunks = await self._vector_store.add(
                    ids=ids,
                    documents=chunk_texts,
                    embeddings=embedding_result.to_lists(),
                    metadatas=metadatas,
                )

                # 4. Update document record
                logger.debug(
                    f"Processing document {document_id}: updating database record status to COMPLETED with {num_chunks} chunks"
                )
                await self._document_repo.update_status(
                    db=db,
                    document_id=document_id,
                    status=DocumentStatus.COMPLETED,
                    num_chunks=num_chunks,
                )

                # Update metadata with extraction info
                await self._document_repo.update_metadata(
                    db=db,
                    document_id=document_id,
                    metadata=doc_metadata.model_dump(exclude_none=True),
                )

                logger.info(f"Document {document_id} processed successfully: {num_chunks} chunks")

                updated_doc = await self._document_repo.get_by_id(db, document_id)
                return DocumentResponse.model_validate(updated_doc)

            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")

                # Update status to failed
                await self._document_repo.update_status(
                    db=db,
                    document_id=document_id,
                    status=DocumentStatus.FAILED,
                    error_message=str(e),
                )

                failed_doc = await self._document_repo.get_by_id(db, document_id)
                return DocumentResponse.model_validate(failed_doc)

    # endregion PROCESSING

    # region READ

    async def get_document(
        self,
        document_id: UUID,
    ) -> DocumentResponse:
        """
        Get a document by ID.
        """
        async with self._uow() as db:

            document = await self._document_repo.get_by_id(db, document_id)
            if not document:
                raise DocumentNotFoundError(str(document_id))
            return DocumentResponse.model_validate(document)

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
        async with self._uow() as db:
            documents = await self._document_repo.get_all(
                db=db,
                skip=skip,
                limit=limit,
                status=status,
                file_type=file_type,
            )
            total = await self._document_repo.count(db, status=status)

            return DocumentList(
                documents=[DocumentResponse.model_validate(doc) for doc in documents],
                total=total,
                skip=skip,
                limit=limit,
            )

    async def get_stats(self) -> DocumentStats:
        """
        Get document statistics.
        """

        async with self._uow() as db:

            stats = await self._document_repo.get_stats(db)
            return DocumentStats(**stats)

    # endregion READ

    # region DELETE

    async def delete_document(
        self,
        document_id: UUID,
    ) -> bool:
        """
        Delete a document and its chunks.
        """
        async with self._uow() as db:
            # Get document
            document = await self._document_repo.get_by_id(db, document_id)
            if not document:
                raise DocumentNotFoundError(str(document_id))

            # Delete chunks from vector store
            try:
                deleted_chunks = await self._vector_store.delete(where={"document_id": str(document_id)})
                logger.debug(f"Deleted {deleted_chunks} chunks for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to delete chunks for document {document_id}: {e}")

            # Delete file using storage backend
            try:
                await self._file_storage.delete(document.file_path)
                logger.debug(f"Deleted file: {document.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file for document {document_id}: {e}")

            # Delete from database
            deleted = await self._document_repo.delete(db, document_id)

            if deleted:
                logger.info(f"Document {document_id} deleted")

            return deleted

    # endregion DELETE
