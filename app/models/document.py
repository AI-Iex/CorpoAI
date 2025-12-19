from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.core.enums import DocumentStatus
from app.db.base import Base


class Document(Base):
    """Document metadata model (chunks stored in ChromaDB)"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # File info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)

    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)

    # RAG availability
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Chunk info (for sync with ChromaDB)
    num_chunks = Column(Integer, nullable=True)
    chroma_collection = Column(String(100), default="documents")

    # Additional metadata (metadata_ to avoid SQLAlchemy reserved name collision)
    metadata_ = Column("metadata", JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_documents_user_status", "user_id", "status"),
        Index("ix_documents_created", "created_at"),
    )
