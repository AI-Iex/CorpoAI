from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.core.enums import StreamEventType


class StreamChunk(BaseModel):
    """Single chunk in a streaming response (SSE format)."""

    event: StreamEventType = Field(..., description="Type of streaming event")
    data: str = Field("", description="Event data (token text, status message, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "event": "status",
                    "data": "Searching in documents...",
                    "metadata": None,
                },
                {
                    "event": "source",
                    "data": "employee_handbook.pdf",
                    "metadata": {
                        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "score": 0.87,
                        "chunk_index": 5,
                    },
                },
                {
                    "event": "token",
                    "data": "Hello",
                    "metadata": None,
                },
                {
                    "event": "done",
                    "data": "",
                    "metadata": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "tokens_used": 156,
                        "latency_ms": 1234.56,
                        "sources_count": 2,
                    },
                },
                {
                    "event": "error",
                    "data": "LLM service unavailable",
                    "metadata": {"code": "LLM_ERROR"},
                },
            ]
        }
    )


class StreamDoneMetadata(BaseModel):
    """Metadata sent with the 'done' event."""

    session_id: UUID = Field(..., description="Session UUID")
    message_id: UUID = Field(..., description="Assistant message UUID")
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed")
    latency_ms: Optional[float] = Field(None, description="Total response time in ms")
    sources_count: int = Field(0, description="Number of RAG sources used")

    model_config = ConfigDict(from_attributes=True)
