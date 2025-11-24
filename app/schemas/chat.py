from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from app.core.enums import MessageRoleTypes

# region MESSAGE


class MessageBase(BaseModel):
    """Base schema for messages"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The message content",
        json_schema_extra={"example": "Hi Corpo! What is the company's vacation policy?"},
    )


class MessageCreate(MessageBase):
    """Schema for creating a new message"""

    session_id: Optional[UUID] = Field(
        None,
        description="Session ID to continue conversation. If None, a new session is created",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    user_id: Optional[UUID] = Field(
        None,
        description="User ID (Optional, only if using IAM_Service with AUTH_ENABLED=true)",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    stream: bool = Field(False, description="Enable streaming response")


class SourceReference(BaseModel):
    """Reference to a document source used in RAG"""

    document_id: UUID = Field(..., description="Document UUID")
    document_name: str = Field(..., description="Original filename")
    chunk_index: int = Field(..., ge=0, description="Chunk index in the document")
    page: Optional[int] = Field(None, ge=1, description="Page number (if applicable)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "document_name": "employee_handbook.pdf",
                "chunk_index": 5,
                "page": 12,
                "score": 0.87,
            }
        }
    )


class ToolCall(BaseModel):
    """Information about a tool execution"""

    name: str = Field(..., description="Tool name")
    arguments: dict = Field(..., description="Tool arguments")
    result: Optional[dict] = Field(None, description="Tool execution result")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "get_user",
                "arguments": {"user_id": "550e8400-e29b-41d4-a716-446655440000"},
                "result": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Name Surname",
                    "email": "email@example.com",
                },
            }
        }
    )


class UserMessageResponse(MessageBase):
    """Response schema for a user message (simplified, no sources/tools)"""

    message_id: UUID = Field(..., description="Message UUID")
    session_id: UUID = Field(..., description="Session UUID")
    role: MessageRoleTypes = Field(MessageRoleTypes.USER, description="Message role (always 'user')")
    created_at: datetime = Field(..., description="Message creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "What is the company's vacation policy?",
                "created_at": "2025-11-24T10:29:58Z",
            }
        },
    )


class AssistantMessageResponse(MessageBase):
    """Response schema for an assistant message (with sources and tools)"""

    message_id: UUID = Field(..., description="Message UUID")
    session_id: UUID = Field(..., description="Session UUID")
    role: MessageRoleTypes = Field(MessageRoleTypes.ASSISTANT, description="Message role (always 'assistant')")
    sources: Optional[List[SourceReference]] = Field(None, description="Document sources used in RAG")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tools executed during this response")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed by LLM")
    latency_ms: Optional[float] = Field(None, ge=0, description="Response time in milliseconds")
    created_at: datetime = Field(..., description="Message creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
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
                    }
                ],
                "tool_calls": None,
                "tokens_used": 156,
                "latency_ms": 1234.56,
                "created_at": "2025-11-24T10:30:00Z",
            }
        },
    )


class ChatResponse(BaseModel):
    """Complete chat interaction response"""

    session_id: UUID = Field(..., description="Session UUID (same for both messages)")
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
                    "created_at": "2025-11-24T10:29:58Z",
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
                    "created_at": "2025-11-24T10:30:00Z",
                },
            }
        },
    )


MessageResponse = UserMessageResponse | AssistantMessageResponse

# endregion MESSAGE

# region SESSION


class SessionBase(BaseModel):
    """Base schema for sessions"""

    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Session title (auto-generated if not provided)",
        json_schema_extra={"example": "Discussion about vacation policy"},
    )


class SessionCreate(SessionBase):
    """Schema for creating a new session"""

    user_id: Optional[UUID] = Field(
        None,
        description="User ID (Optional, only if using IAM_Service with AUTH_ENABLED=true)",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )


class SessionUpdate(BaseModel):
    """Schema for updating a session"""

    title: Optional[str] = Field(None, max_length=200, description="New session title")


class SessionInfo(BaseModel):
    """Detailed session information"""

    id: UUID = Field(..., description="Session UUID")
    user_id: Optional[UUID] = Field(None, description="User ID (if authenticated)")
    title: str = Field(..., description="Session title")
    message_count: int = Field(..., ge=0, description="Number of messages in this session")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "2d661112-5af7-494e-b528-8a15c0bb93b3",
                "title": "HR Policy Questions",
                "message_count": 8,
                "created_at": "2025-11-24T09:00:00Z",
                "updated_at": "2025-11-24T10:30:00Z",
            }
        },
    )


class SessionList(BaseModel):
    """List of sessions with pagination"""

    sessions: List[SessionInfo] = Field(..., description="List of sessions")
    total: int = Field(..., ge=0, description="Total number of sessions")
    skip: int = Field(..., ge=0, description="Number of sessions skipped")
    limit: int = Field(..., ge=1, description="Maximum sessions returned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "user_12345",
                        "title": "HR Policy Questions",
                        "message_count": 8,
                        "created_at": "2025-11-24T09:00:00Z",
                        "updated_at": "2025-11-24T10:30:00Z",
                    }
                ],
                "total": 25,
                "skip": 0,
                "limit": 50,
            }
        }
    )


class SessionHistory(BaseModel):
    """Session with full message history"""

    session: SessionInfo = Field(..., description="Session information")
    messages: List[UserMessageResponse | AssistantMessageResponse] = Field(
        ..., description="All messages in chronological order"
    )

    model_config = ConfigDict(from_attributes=True)


# endregion SESSION
