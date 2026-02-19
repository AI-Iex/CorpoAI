from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolParameter(BaseModel):
    """Schema for a single tool parameter."""

    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    description: str = Field("", description="Parameter description")
    enum: Optional[list[str]] = Field(None, description="Allowed values for enum types")
    default: Optional[Any] = Field(None, description="Default value if not provided")
    items: Optional[dict] = Field(None, description="Schema for array items")

    model_config = ConfigDict(extra="allow")


class ToolParameters(BaseModel):
    """JSON Schema for tool parameters."""

    type: str = Field("object", description="Always 'object' for tool parameters")
    properties: dict[str, ToolParameter | dict] = Field(
        default_factory=dict, description="Parameter definitions"
    )
    required: list[str] = Field(default_factory=list, description="Required parameter names")

    model_config = ConfigDict(extra="allow")


class ToolDefinition(BaseModel):
    """
    Internal tool definition format.

    Loaded from database, used by all LLM clients.
    Each client converts this to their specific format.
    """

    name: str = Field(..., description="Unique tool name (snake_case)")
    description: str = Field(..., description="What the tool does (for LLM)")
    parameters: ToolParameters = Field(
        default_factory=lambda: ToolParameters(type="object"),
        description="Tool parameters schema",
    )
    required_permissions: list[str] = Field(
        default_factory=list, description="Permissions needed to use this tool"
    )
    is_builtin: bool = Field(
        True, description="Whether this is a builtin tool with Python implementation"
    )
    is_enabled: bool = Field(
        True, description="Whether the tool is currently enabled"
    )
    # External tool config
    endpoint: Optional[str] = Field(None, description="HTTP endpoint for external tools")
    http_method: str = Field("POST", description="HTTP method for external tools")
    headers: Optional[dict[str, str]] = Field(None, description="HTTP headers for external tools")
    timeout: int = Field(30, description="Request timeout in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius",
                        },
                    },
                    "required": ["city"],
                },
                "required_permissions": [],
                "is_builtin": True,
            }
        }
    )

    def to_json_schema(self) -> dict:
        """Convert parameters to JSON Schema format for LLM."""
        return {
            "type": self.parameters.type,
            "properties": {
                name: param.model_dump(exclude_none=True) if isinstance(param, ToolParameter) else param
                for name, param in self.parameters.properties.items()
            },
            "required": self.parameters.required,
        }

    @classmethod
    def from_db_model(cls, tool) -> "ToolDefinition":
        """Create ToolDefinition from database Tool model."""
        return cls(
            name=tool.name,
            description=tool.description,
            parameters=ToolParameters(**tool.parameters) if tool.parameters else ToolParameters(type="object"),
            required_permissions=tool.required_permissions or [],
            is_builtin=tool.is_builtin,
            is_enabled=tool.is_enabled,
            endpoint=tool.endpoint,
            http_method=tool.http_method or "POST",
            headers=tool.headers,
            timeout=tool.timeout or 30,
        )


class ToolCall(BaseModel):
    """
    Represents a tool call request from the LLM.

    Each LLM client parses their response format into this.
    """

    id: Optional[str] = Field(None, description="Unique call ID (from LLM)")
    name: str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "call_abc123",
                "name": "get_weather",
                "arguments": {"city": "Madrid", "units": "celsius"},
            }
        }
    )


class ToolResult(BaseModel):
    """
    Result from executing a tool.

    Returned to the LLM for further processing.
    """

    tool_call_id: Optional[str] = Field(None, description="Original call ID")
    name: str = Field(..., description="Tool name that was called")
    success: bool = Field(..., description="Whether execution succeeded")
    result: Any = Field(None, description="Tool output (any JSON-serializable value)")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tool_call_id": "call_abc123",
                    "name": "get_weather",
                    "success": True,
                    "result": {
                        "city": "Madrid",
                        "temperature": 22,
                        "condition": "Sunny",
                        "humidity": 45,
                    },
                    "error": None,
                },
                {
                    "tool_call_id": "call_xyz789",
                    "name": "get_weather",
                    "success": False,
                    "result": None,
                    "error": "City not found: Madrdi",
                },
            ]
        }
    )

    def to_message_content(self) -> str:
        """Format result as string for LLM context."""
        if self.success:
            if isinstance(self.result, dict):
                import json

                return json.dumps(self.result, indent=2, ensure_ascii=False)
            return str(self.result)
        return f"Error: {self.error}"
