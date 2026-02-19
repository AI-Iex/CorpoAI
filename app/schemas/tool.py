from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ToolParameterSchema(BaseModel):
    """Schema for tool parameter definition."""

    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    description: str = Field("", description="Parameter description")
    enum: Optional[List[str]] = Field(None, description="Allowed values for enum types")
    default: Optional[Any] = Field(None, description="Default value")

    model_config = ConfigDict(extra="allow")


class ToolParametersSchema(BaseModel):
    """JSON Schema for tool parameters."""

    type: str = Field("object", description="Always 'object' for tool parameters")
    properties: dict[str, ToolParameterSchema | dict] = Field(
        default_factory=dict, description="Parameter definitions"
    )
    required: List[str] = Field(default_factory=list, description="Required parameter names")


# region CREATE


class ToolCreate(BaseModel):
    """Schema for creating a new tool."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique tool name (snake_case)",
    )
    description: str = Field(..., min_length=1, description="Tool description for LLM")
    parameters: ToolParametersSchema = Field(
        default_factory=lambda: ToolParametersSchema(type="object"),
        description="Tool parameters schema",
    )
    is_builtin: bool = Field(False, description="Whether this is a builtin tool")
    is_enabled: bool = Field(True, description="Whether the tool is enabled")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for external tools")
    http_method: str = Field("POST", description="HTTP method for external tools")
    headers: Optional[dict] = Field(None, description="HTTP headers for external tools")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    required_permissions: List[str] = Field(
        default_factory=list, description="Permissions required to use this tool"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                "is_builtin": False,
                "is_enabled": True,
                "endpoint": "https://api.example.com/search",
                "http_method": "POST",
                "timeout": 30,
                "required_permissions": [],
            }
        }
    )


# endregion CREATE

# region UPDATE


class ToolUpdate(BaseModel):
    """Schema for updating a tool."""

    description: Optional[str] = Field(None, min_length=1, description="Tool description")
    parameters: Optional[ToolParametersSchema] = Field(None, description="Tool parameters schema")
    is_enabled: Optional[bool] = Field(None, description="Whether the tool is enabled")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for external tools")
    http_method: Optional[str] = Field(None, description="HTTP method for external tools")
    headers: Optional[dict] = Field(None, description="HTTP headers for external tools")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Request timeout in seconds")
    required_permissions: Optional[List[str]] = Field(
        None, description="Permissions required to use this tool"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated description",
                "is_enabled": False,
                "timeout": 60,
            }
        }
    )


class ToolSetEnabled(BaseModel):
    """Schema for enabling/disabling a tool."""

    is_enabled: bool = Field(..., description="Whether the tool should be enabled")


# endregion UPDATE

# region RESPONSE


class ToolResponse(BaseModel):
    """Schema for tool response."""

    id: UUID = Field(..., description="Tool ID")
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict = Field(..., description="Tool parameters schema")
    is_builtin: bool = Field(..., description="Whether this is a builtin tool")
    is_enabled: bool = Field(..., description="Whether the tool is enabled")
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for external tools")
    http_method: Optional[str] = Field(None, description="HTTP method")
    timeout: Optional[int] = Field(None, description="Request timeout")
    required_permissions: List[str] = Field(..., description="Required permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
                "is_builtin": True,
                "is_enabled": True,
                "endpoint": None,
                "http_method": "POST",
                "timeout": 30,
                "required_permissions": [],
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": None,
            }
        }
    )


class ToolListResponse(BaseModel):
    """Schema for paginated tool list."""

    tools: List[ToolResponse] = Field(..., description="List of tools")
    total: int = Field(..., description="Total number of tools")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Maximum items per page")


# endregion RESPONSE
