from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.enums import MessageRoleTypes
from app.db.base import Base


class Message(Base):
    """Chat message model"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRoleTypes), nullable=False)
    content = Column(Text, nullable=False)

    # RAG metadata
    sources = Column(JSONB, nullable=True)

    # Tool execution metadata
    tool_calls = Column(JSONB, nullable=True)

    # Performance metrics
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")

    __table_args__ = (Index("ix_messages_session_created", "session_id", "created_at"),)
