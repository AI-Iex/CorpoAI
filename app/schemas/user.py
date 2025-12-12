from pydantic import BaseModel, Field
from typing import List, Optional


class User(BaseModel):
    """User Schema."""

    sub: str = Field(..., description="Subject (User or Client ID)")
    type: str = Field(default="user", description="Token type: 'user' or 'client'")
    permissions: List[str] = Field(default_factory=list, description="User/Client permissions")
    is_superuser: bool = Field(default=False, description="Superuser flag")
    require_password_change: bool = Field(
        default=False, description="Indicates if the user must change password before proceeding"
    )
    client_id: Optional[str] = Field(default=None, description="Client ID (for client tokens)")

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "123e4567-e89b-12d3-a456-426614174000",
                "type": "user",
                "permissions": ["chat:read", "chat:write", "documents:read"],
                "is_superuser": False,
                "require_password_change": False,
                "client_id": None,
            }
        }
