from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.enums import DocumentStatus, DocumentTypeFile


# region EMBEDDED SCHEMAS


class DocumentMetadata(BaseModel):
    """Document metadata extracted during processing."""

    # Document info
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")

    # Structure info
    pages: Optional[int] = Field(None, ge=1, description="Number of pages (PDF)")
    paragraphs: Optional[int] = Field(None, ge=1, description="Number of paragraphs (DOCX)")
    lines: Optional[int] = Field(None, ge=1, description="Number of lines (TXT/MD)")

    # File info (added during extraction)
    file_name: Optional[str] = Field(None, description="Original file name")
    file_type: Optional[str] = Field(None, description="File extension")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    char_count: Optional[int] = Field(None, ge=0, description="Total character count")
    encoding: Optional[str] = Field(None, description="Detected encoding (TXT/MD)")

    # Additional metadata
    language: Optional[str] = Field(None, description="Detected language (ISO 639-1)")
    created_date: Optional[datetime] = Field(None, description="Original document creation date")
    modified_date: Optional[datetime] = Field(None, description="Original document modification date")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "author": "HR Department",
                "title": "Employee Handbook 2025",
                "pages": 45,
                "file_name": "handbook.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "char_count": 125000,
                "language": "en",
                "created_date": "2025-01-15T00:00:00Z",
                "keywords": ["policy", "vacation", "benefits"],
            }
        }
    )


class ChunkMetadata(BaseModel):
    """Metadata for a single text chunk."""

    chunk_index: int = Field(..., ge=0, description="Index of this chunk")
    chunk_length: int = Field(..., ge=0, description="Length of chunk text in characters")

    # Inherited from document metadata
    file_name: Optional[str] = Field(None, description="Source file name")
    file_type: Optional[str] = Field(None, description="Source file type")
    pages: Optional[int] = Field(None, description="Total pages in source")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_index": 0,
                "chunk_length": 512,
                "file_name": "handbook.pdf",
                "file_type": "pdf",
                "pages": 45,
            }
        }
    )


class TextChunk(BaseModel):
    """A single text chunk with metadata."""

    text: str = Field(..., description="Chunk text content")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "This is the content of the chunk...",
                "metadata": {
                    "chunk_index": 0,
                    "chunk_length": 512,
                    "file_name": "handbook.pdf",
                },
            }
        }
    )


class ChunkInfo(BaseModel):
    """Information about document chunks in ChromaDB."""

    total_chunks: int = Field(..., ge=0, description="Total number of chunks")
    avg_chunk_size: Optional[int] = Field(None, ge=0, description="Average chunk size in characters")
    collection_name: str = Field(..., description="ChromaDB collection name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_chunks": 127,
                "avg_chunk_size": 512,
                "collection_name": "documents",
            }
        }
    )


# endregion EMBEDDED SCHEMAS

# region UPLOAD


class DocumentUpload(BaseModel):
    """Schema for document upload request (metadata only, file sent separately)."""

    user_id: Optional[UUID] = Field(
        None,
        description="User ID (optional, used when AUTH_ENABLED=true)",
    )
    collection: Optional[str] = Field(
        "documents",
        max_length=100,
        description="ChromaDB collection name",
    )
    metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Optional metadata to attach",
    )


# endregion UPLOAD

# region RESPONSE


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID = Field(..., description="Document UUID")
    user_id: Optional[UUID] = Field(None, description="User ID (if authenticated)")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentTypeFile = Field(..., description="File type (pdf, docx, txt, md)")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    status: DocumentStatus = Field(..., description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    num_chunks: Optional[int] = Field(None, ge=0, description="Number of chunks created")
    chroma_collection: Optional[str] = Field(None, description="ChromaDB collection name")
    doc_metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Document metadata",
        validation_alias="metadata_",
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator("doc_metadata", mode="before")
    @classmethod
    def validate_metadata(cls, v):
        """Convert dict to DocumentMetadata if needed."""
        if v is None or (isinstance(v, dict) and not v):
            return None
        if isinstance(v, dict):
            return DocumentMetadata(**v)
        return v

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "employee_handbook.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "status": "completed",
                "error_message": None,
                "num_chunks": 127,
                "chroma_collection": "documents",
                "doc_metadata": {
                    "author": "HR Department",
                    "title": "Employee Handbook 2025",
                    "pages": 45,
                },
                "created_at": "2025-11-28T09:00:00Z",
                "updated_at": "2025-11-28T09:05:00Z",
            }
        },
    )

    @property
    def file_size_unit(self) -> str:
        """Return unit-readable file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if self.file_size < 1024:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024
        return f"{self.file_size:.1f} TB"


class DocumentUploadResponse(BaseModel):
    """Response after document upload (before processing completes)."""

    id: UUID = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(DocumentStatus.PENDING, description="Initial status")
    message: str = Field(..., description="Status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "filename": "employee_handbook.pdf",
                "status": "pending",
                "message": "Document uploaded successfully. Processing started.",
            }
        }
    )


# endregion RESPONSE

# region LIST


class DocumentList(BaseModel):
    """Paginated list of documents."""

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total number of documents")
    skip: int = Field(..., ge=0, description="Number of documents skipped")
    limit: int = Field(..., ge=1, description="Maximum documents returned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "filename": "employee_handbook.pdf",
                        "file_type": "pdf",
                        "file_size": 2048576,
                        "status": "completed",
                        "num_chunks": 127,
                        "created_at": "2025-11-28T09:00:00Z",
                    }
                ],
                "total": 15,
                "skip": 0,
                "limit": 50,
            }
        }
    )


# endregion LIST

# region STATS


class DocumentStats(BaseModel):
    """Document storage statistics."""

    total_documents: int = Field(..., ge=0, description="Total documents")
    total_chunks: int = Field(..., ge=0, description="Total chunks across all documents")
    total_size_bytes: int = Field(..., ge=0, description="Total storage used in bytes")
    by_status: dict = Field(..., description="Count by status")
    by_type: dict = Field(..., description="Count by file type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_documents": 25,
                "total_chunks": 3420,
                "total_size_bytes": 52428800,
                "by_status": {
                    "pending": 2,
                    "processing": 1,
                    "completed": 20,
                    "failed": 2,
                },
                "by_type": {
                    "pdf": 15,
                    "docx": 5,
                    "txt": 3,
                    "md": 2,
                },
            }
        }
    )

    @property
    def total_size_human(self) -> str:
        """Return human-readable total size."""
        size = self.total_size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# endregion STATS
