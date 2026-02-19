from abc import ABC, abstractmethod
from typing import Any
from app.tools.schemas import ToolDefinition, ToolCall, ToolResult

class ITool(ABC):
    """
    Interface for tool implementations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name (must match database definition)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with given arguments.
        """
        pass

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and transform arguments before execution.
        Override in subclass for custom validation.
        """
        return args

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class IToolExecutor(ABC):
    """
    Interface for tool executor.
    """

    @abstractmethod
    async def execute(
        self,
        tool_call: ToolCall,
        tool_def: ToolDefinition,
        user_permissions: list[str] | None = None,
    ) -> ToolResult:
        """
        Execute a tool call.
        """
        pass

    @abstractmethod
    async def execute_many(
        self,
        tool_calls: list[tuple[ToolCall, ToolDefinition]],
        user_permissions: list[str] | None = None,
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls.
        """
        pass

    @abstractmethod
    def register_implementation(self, tool: ITool) -> None:
        """
        Register a tool implementation.
        """
        pass

    @abstractmethod
    def has_implementation(self, tool_name: str) -> bool:
        """
        Check if a tool has a registered implementation.
        """
        pass
