from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class Tool(Base):
    """Tool definition stored in database."""

    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tool identity
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Parameters schema (JSON Schema format)
    # Example: {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
    parameters = Column(JSONB, nullable=False, default=dict)

    # Tool type
    is_builtin = Column(Boolean, default=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # External tool configuration (null for builtin tools)
    endpoint = Column(String(500), nullable=True)
    http_method = Column(String(10), default="POST", nullable=True)
    headers = Column(JSONB, nullable=True)  # Custom headers for external calls
    timeout = Column(Integer, default=30, nullable=True)

    # Permissions required to use this tool (empty = public)
    required_permissions = Column(JSONB, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_tools_enabled", "is_enabled"),
        Index("ix_tools_builtin", "is_builtin"),
    )

    def __repr__(self) -> str:
        return f"<Tool {self.name} (enabled={self.is_enabled}, builtin={self.is_builtin})>"

    def to_definition(self) -> dict:
        """Convert to tool definition dict for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters or {},
            "is_builtin": self.is_builtin,
            "is_enabled": self.is_enabled,
            "endpoint": self.endpoint,
            "required_permissions": self.required_permissions or [],
        }
