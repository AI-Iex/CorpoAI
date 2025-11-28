from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# region BASE


class SessionBase(BaseModel):
    """Base schema for sessions."""

    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Session title (auto-generated if not provided)",
        json_schema_extra={"example": "Discussion about vacation policy"},
    )


# endregion BASE

# region CREATE / UPDATE


class SessionCreate(SessionBase):
    """Schema for creating a new session."""

    user_id: Optional[UUID] = Field(
        None,
        description="User ID (optional, used when AUTH_ENABLED=true)",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    title: Optional[str] = Field(
        None,
        max_length=200,
        description="New session title",
        json_schema_extra={"example": "Updated conversation title"},
    )


# endregion CREATE / UPDATE

# region RESPONSE


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: UUID = Field(..., description="Session UUID")
    user_id: Optional[UUID] = Field(None, description="User ID (if authenticated)")
    title: str = Field(..., description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "2d661112-5af7-494e-b528-8a15c0bb93b3",
                "title": "HR Policy Questions",
                "created_at": "2025-11-28T09:00:00Z",
                "updated_at": "2025-11-28T10:30:00Z",
            }
        },
    )


class SessionInfo(SessionResponse):
    """Extended session information with message count."""

    message_count: int = Field(..., ge=0, description="Number of messages in this session")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "2d661112-5af7-494e-b528-8a15c0bb93b3",
                "title": "HR Policy Questions",
                "message_count": 8,
                "created_at": "2025-11-28T09:00:00Z",
                "updated_at": "2025-11-28T10:30:00Z",
            }
        },
    )


# endregion RESPONSE

# region LIST


class SessionList(BaseModel):
    """Paginated list of sessions."""

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
                        "user_id": "2d661112-5af7-494e-b528-8a15c0bb93b3",
                        "title": "HR Policy Questions",
                        "message_count": 8,
                        "created_at": "2025-11-28T09:00:00Z",
                        "updated_at": "2025-11-28T10:30:00Z",
                    }
                ],
                "total": 25,
                "skip": 0,
                "limit": 50,
            }
        }
    )


# endregion LIST
