from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class Session(Base):
    """Chat session model"""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    title = Column(String(200), nullable=False, default="Nueva conversación")

    # Summary for context management
    summary = Column(Text, nullable=True)
    summary_up_to_message_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata_ = Column("metadata", JSONB, default={})

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_sessions_user_created", "user_id", "created_at"),)
