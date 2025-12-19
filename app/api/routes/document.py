import logging
from pathlib import Path as FilePath
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Path, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from app.dependencies.services import get_document_service
from app.services.interfaces.document import IDocumentService
from app.core.config import settings
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentList,
    DocumentStats,
    DocumentToggleEnabled,
)
from app.schemas.user import User
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions
from app.core.enums import DocumentStatus, DocumentTypeFile
from app.core.exceptions import DocumentNotFoundError
from app.tasks.document_processing import process_document_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# region UPLOAD


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document",
    description=(
        "**Upload a document for processing.**\n\n"
        f"Supported formats: {', '.join([e.value for e in DocumentTypeFile])}\n\n"
        "The document is uploaded and queued for background processing. "
        "Processing includes text extraction, chunking, embedding generation, "
        "and storage in the vector database.\n\n"
        "Use the document ID to check processing status."
    ),
    response_description="Upload confirmation with document ID",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload"),
    collection: str = Query("documents", description="ChromaDB collection name"),
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_UPLOAD)),
) -> DocumentUploadResponse:
    """Upload a document for RAG processing."""

    user_id = user.sub if user else None

    # Upload and validate the document
    response = await document_service.upload(
        file=file,
        user_id=user_id,
        collection=collection,
    )

    # Queue background processing
    background_tasks.add_task(process_document_task, response.id)

    return response


# endregion UPLOAD


# region READ


@router.get(
    "",
    response_model=DocumentList,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description=(
        "**Get a paginated list of all documents.**\n\n"
        "Documents are sorted by creation date (newest first).\n\n"
        "- `skip` indicates how many documents to skip.\n"
        "- `limit` specifies the maximum number to return.\n"
        "- `status` to filter by processing status.\n"
        "- `file_type` to filter by document file type: pdf, txt, md, docx..."
    ),
    response_description="Paginated list of documents",
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum documents to return"),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status", description="Filter by status"),
    file_type: Optional[DocumentTypeFile] = Query(None, description="Filter by file type"),
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_LIST)),
) -> DocumentList:
    """List all documents with pagination."""

    return await document_service.get_documents(
        skip=skip,
        limit=limit,
        status=status_filter,
        file_type=file_type,
    )


@router.get(
    "/stats",
    response_model=DocumentStats,
    status_code=status.HTTP_200_OK,
    summary="Get document statistics",
    description="**Get statistics about stored documents.**",
    response_description="Document storage statistics",
)
async def get_document_stats(
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_STATS)),
) -> DocumentStats:
    """Get document statistics."""
    return await document_service.get_stats()


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description=(
        "**Get detailed information about a specific document.**\n\n"
        "Includes processing status, chunk count, and metadata."
    ),
    response_description="Document details",
)
async def get_document(
    document_id: UUID = Path(..., description="Document UUID"),
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_READ)),
) -> DocumentResponse:
    """Get a document by ID."""
    return await document_service.get_document(document_id)


@router.get(
    "/{document_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download a document",
    description=("**Download the original document file.**\n\n" "Returns the original uploaded file for download."),
    response_class=FileResponse,
)
async def download_document(
    document_id: UUID = Path(..., description="Document UUID"),
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_DOWNLOAD)),
) -> FileResponse:
    """Download a document file."""

    # Get file info from service
    document_file_info = await document_service.get_document(document_id)

    # Build full file path
    file_path = FilePath(settings.DOCUMENTS_STORAGE_PATH) / document_file_info.file_path

    return FileResponse(
        path=file_path,
        filename=document_file_info.filename,
    )


# endregion READ


# region UPDATE


@router.patch(
    "/{document_id}/enabled",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable or disable a document for RAG",
    description=(
        "**Toggle document availability for RAG retrieval.**\n\n"
        "When disabled, the document's chunks will not be included in "
        "semantic search results, effectively excluding it from AI responses.\n\n"
        "The document and its chunks remain stored and can be re-enabled at any time."
    ),
    response_description="Updated document details",
)
async def toggle_document_enabled(
    document_id: UUID = Path(..., description="Document UUID"),
    body: DocumentToggleEnabled = ...,
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_UPDATE)),
) -> DocumentResponse:
    """Enable or disable a document for RAG retrieval."""
    return await document_service.set_enabled(document_id, body.is_enabled)


# endregion UPDATE


# region DELETE


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description=(
        "**Delete a document and all its chunks.**\n\n"
        "Removes the document from PostgreSQL, its chunks from ChromaDB, "
        "and the source file from storage."
    ),
)
async def delete_document(
    document_id: UUID = Path(..., description="Document UUID"),
    document_service: IDocumentService = Depends(get_document_service),
    user: Optional[User] = Depends(requires_permission(Permissions.DOCUMENTS_DELETE)),
) -> None:
    """Delete a document and its chunks."""
    return await document_service.delete_document(document_id)


# endregion DELETE
