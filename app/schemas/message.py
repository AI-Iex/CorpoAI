from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.core.enums import MessageRoleTypes


# region EMBEDDED SCHEMAS


class SourceReference(BaseModel):
    """Reference to a document source used in RAG."""

    document_id: UUID = Field(..., description="Document UUID")
    document_name: str = Field(..., description="Original filename")
    chunk_index: int = Field(..., ge=0, description="Chunk index in the document")
    page: Optional[int] = Field(None, ge=1, description="Page number (if applicable)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    text_preview: Optional[str] = Field(
        None,
        max_length=200,
        description="Short preview of the matched text",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "document_name": "employee_handbook.pdf",
                "chunk_index": 5,
                "page": 12,
                "score": 0.87,
                "text_preview": "Employees are entitled to 15 vacation days...",
            }
        }
    )


class ToolCall(BaseModel):
    """Information about a tool execution."""

    name: str = Field(..., description="Tool name")
    arguments: dict = Field(..., description="Tool arguments")
    result: Optional[dict] = Field(None, description="Tool execution result")
    status: Optional[str] = Field(
        "success",
        description="Execution status: success, error, timeout",
    )
    duration_ms: Optional[float] = Field(None, ge=0, description="Execution time in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "get_user",
                "arguments": {"user_id": "550e8400-e29b-41d4-a716-446655440000"},
                "result": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                },
                "status": "success",
                "duration_ms": 45.2,
            }
        }
    )


# endregion EMBEDDED SCHEMAS

# region BASE


class MessageBase(BaseModel):
    """Base schema for messages."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="The message content",
        json_schema_extra={"example": "What is the company's vacation policy?"},
    )


# endregion BASE

# region CREATE


class MessageCreate(MessageBase):
    """Schema for creating a new message (user input)."""

    session_id: Optional[UUID] = Field(
        None,
        description="Session ID to continue conversation. If None, a new session is created",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    user_id: Optional[UUID] = Field(
        None,
        description="User ID (optional, used when AUTH_ENABLED=true)",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    stream: bool = Field(False, description="Enable streaming response")


class MessageCreateInternal(MessageBase):
    """Internal schema for creating messages (used by services)."""

    session_id: UUID = Field(..., description="Session ID")
    role: MessageRoleTypes = Field(..., description="Message role")
    sources: Optional[List[SourceReference]] = Field(None, description="RAG sources")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool executions")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed")
    latency_ms: Optional[float] = Field(None, ge=0, description="Response latency")


# endregion CREATE

# region RESPONSE


class MessageResponse(MessageBase):
    """Base response schema for messages."""

    id: UUID = Field(..., alias="message_id", description="Message UUID")
    session_id: UUID = Field(..., description="Session UUID")
    role: MessageRoleTypes = Field(..., description="Message role")
    created_at: datetime = Field(..., description="Message creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class UserMessageResponse(MessageResponse):
    """Response schema for a user message."""

    role: MessageRoleTypes = Field(
        MessageRoleTypes.USER,
        description="Message role (always 'user')",
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "What is the company's vacation policy?",
                "created_at": "2025-11-28T10:29:58Z",
            }
        },
    )


class AssistantMessageResponse(MessageResponse):
    """Response schema for an assistant message."""

    role: MessageRoleTypes = Field(
        MessageRoleTypes.ASSISTANT,
        description="Message role (always 'assistant')",
    )
    sources: Optional[List[SourceReference]] = Field(
        None,
        description="Document sources used in RAG",
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="Tools executed during this response",
    )
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed by LLM")
    latency_ms: Optional[float] = Field(None, ge=0, description="Response time in milliseconds")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "According to the employee handbook, you have 15 vacation days per year.",
                "sources": [
                    {
                        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "document_name": "employee_handbook.pdf",
                        "chunk_index": 5,
                        "page": 12,
                        "score": 0.87,
                        "text_preview": "Employees are entitled to 15 vacation days...",
                    }
                ],
                "tool_calls": None,
                "tokens_used": 156,
                "latency_ms": 1234.56,
                "created_at": "2025-11-28T10:30:00Z",
            }
        },
    )


# endregion RESPONSE

# region CHAT RESPONSE


class ChatResponse(BaseModel):
    """Complete chat interaction response."""

    session_id: UUID = Field(..., description="Session UUID")
    user_message: UserMessageResponse = Field(..., description="User's message")
    assistant_message: AssistantMessageResponse = Field(..., description="Assistant's response")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_message": {
                    "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "user",
                    "content": "What is the vacation policy?",
                    "created_at": "2025-11-28T10:29:58Z",
                },
                "assistant_message": {
                    "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "assistant",
                    "content": "You have 15 vacation days per year.",
                    "sources": [
                        {
                            "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                            "document_name": "employee_handbook.pdf",
                            "chunk_index": 5,
                            "page": 12,
                            "score": 0.87,
                        }
                    ],
                    "tool_calls": None,
                    "tokens_used": 156,
                    "latency_ms": 1234.56,
                    "created_at": "2025-11-28T10:30:00Z",
                },
            }
        },
    )


# endregion CHAT RESPONSE

# region HISTORY


class SessionHistory(BaseModel):
    """Session with full message history."""

    session_id: UUID = Field(..., description="Session UUID")
    title: str = Field(..., description="Session title")
    message_count: int = Field(..., ge=0, description="Total messages")
    messages: List[UserMessageResponse | AssistantMessageResponse] = Field(
        ...,
        description="All messages in chronological order",
    )
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# endregion HISTORY
