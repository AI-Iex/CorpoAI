from abc import ABC, abstractmethod
from typing import List

from app.tools.schemas import ToolDefinition, ToolCall, ToolResult


class IToolsService(ABC):
    """Interface for tools service."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the tools service."""
        pass

    @abstractmethod
    async def get_tools(self, user_permissions: List[str] | None = None) -> List[ToolDefinition]:
        """Get available tools for a user."""
        pass

    @abstractmethod
    async def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        pass

    @abstractmethod
    async def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a specific tool by name."""
        pass

    @abstractmethod
    async def execute(
        self,
        tool_call: ToolCall,
        user_permissions: List[str] | None = None,
    ) -> ToolResult:
        """Execute a tool call."""
        pass

    @property
    @abstractmethod
    def tool_count(self) -> int:
        """Number of registered tools."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether service has been initialized."""
        pass
        """Whether service has been initialized."""
        pass
