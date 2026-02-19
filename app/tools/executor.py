import logging
from typing import Any
import httpx
from app.tools.interfaces import IToolExecutor, ITool
from app.tools.schemas import ToolCall, ToolResult, ToolDefinition
from app.core.config import settings
from app.core.exceptions import ToolExecutionError, ToolNotFoundError

logger = logging.getLogger(__name__)

class ToolExecutor(IToolExecutor):
    """
    Executes tools and manages tool implementations.
    """

    def __init__(self):
        """Initialize the executor."""
        self._implementations: dict[str, ITool] = {}
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for external tool calls."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=settings.TOOLS_TIMEOUT)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def register_implementation(self, tool: ITool) -> None:
        """Register a builtin tool implementation."""
        self._implementations[tool.name] = tool
        logger.debug(f"Registered tool implementation: {tool.name}")

    def has_implementation(self, tool_name: str) -> bool:
        """Check if a tool has a registered implementation."""
        return tool_name in self._implementations

    async def execute(
        self,
        tool_call: ToolCall,
        tool_def: ToolDefinition,
        user_permissions: list[str] | None = None,
    ) -> ToolResult:
        """
        Execute a single tool call.
        """
        # Check permissions
        if not self._check_permissions(tool_def, user_permissions):
            logger.warning(f"Permission denied for tool: {tool_call.name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=False,
                error=f"Permission denied for tool '{tool_call.name}'",
            )

        # Check if tool is enabled
        if not tool_def.is_enabled:
            logger.warning(f"Tool is disabled: {tool_call.name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=False,
                error=f"Tool '{tool_call.name}' is currently disabled",
            )

        # Execute based on tool type
        try:
            if tool_def.is_builtin:
                result = await self._execute_builtin(tool_call, tool_def)
            else:
                result = await self._execute_external(tool_call, tool_def)

            logger.info(f"Tool executed successfully: {tool_call.name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=True,
                result=result,
            )

        except ToolExecutionError as e:
            logger.error(f"Tool execution error: {tool_call.name} - {e}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error executing tool {tool_call.name}: {e}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=False,
                error=f"Internal error: {type(e).__name__}",
            )

    async def execute_many(
        self,
        tool_calls: list[tuple[ToolCall, ToolDefinition]],
        user_permissions: list[str] | None = None,
    ) -> list[ToolResult]:
        """Execute multiple tool calls sequentially."""
        results = []
        for call, tool_def in tool_calls:
            result = await self.execute(call, tool_def, user_permissions)
            results.append(result)
        return results

    def _check_permissions(
        self, tool_def: ToolDefinition, user_permissions: list[str] | None
    ) -> bool:
        """Check if user has permission to use the tool."""
        # No permissions required
        if not tool_def.required_permissions:
            return True

        # No user permissions provided (anonymous)
        if not user_permissions:
            return False

        # Check if user has at least one required permission
        return any(perm in user_permissions for perm in tool_def.required_permissions)

    async def _execute_builtin(self, tool_call: ToolCall, tool_def: ToolDefinition) -> Any:
        """Execute a builtin tool using registered Python implementation."""
        impl = self._implementations.get(tool_call.name)
        if not impl:
            raise ToolNotFoundError(
                f"No implementation registered for builtin tool '{tool_call.name}'"
            )

        # Validate arguments
        validated_args = impl.validate_args(tool_call.arguments)

        # Execute
        return await impl.execute(**validated_args)

    async def _execute_external(self, tool_call: ToolCall, tool_def: ToolDefinition) -> Any:
        """Execute an external tool via HTTP request."""
        if not tool_def.endpoint:
            raise ToolExecutionError(
                f"No endpoint configured for external tool '{tool_call.name}'"
            )

        client = await self._get_http_client()

        try:
            response = await client.request(
                method=tool_def.http_method,
                url=tool_def.endpoint,
                json=tool_call.arguments,
                headers=tool_def.headers or {},
                timeout=tool_def.timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise ToolExecutionError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise ToolExecutionError(f"Request failed: {e}")
