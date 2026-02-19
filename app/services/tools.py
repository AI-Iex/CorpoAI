import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.tools.schemas import ToolDefinition, ToolCall, ToolResult
from app.tools.executor import ToolExecutor
from app.tools.interfaces import ITool
from app.tools.builtin import WeatherTool, DateTimeTool, CurrencyTool
from app.repositories.interfaces.tool import IToolRepository
from app.repositories.tool import ToolRepository
from app.services.interfaces.tools import IToolsService
from app.db.unit_of_work import UnitOfWorkFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


class ToolsService(IToolsService):
    """
    Service for managing and executing tools.
    """

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        tool_repo: IToolRepository | None = None,
        executor: ToolExecutor | None = None,
    ):
        self._uow = uow_factory
        self._repo = tool_repo or ToolRepository()
        self._executor = executor or ToolExecutor()
        self._cache: List[ToolDefinition] = []
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the tools service.
        """
        if self._initialized:
            return

        # Register builtin tool implementations
        self._register_builtin_tools()

        # Load tools from database into cache
        await self._refresh_cache()

        self._initialized = True
        logger.info(f"Tools service initialized with {len(self._cache)} tools")

    def _register_builtin_tools(self) -> None:
        """Register all builtin tool implementations."""
        builtin_tools: List[ITool] = [
            WeatherTool(),
            DateTimeTool(),
            CurrencyTool(),
        ]

        for tool in builtin_tools:
            self._executor.register_implementation(tool)
            logger.debug(f"Registered builtin tool implementation: {tool.name}")

    async def _refresh_cache(self) -> None:
        """Reload tools from database into cache."""
        async with self._uow() as db:
            tools = await self._repo.get_enabled(db)
            self._cache = [ToolDefinition.from_db_model(t) for t in tools]
            logger.debug(f"Tools cache refreshed: {len(self._cache)} tools")

    async def refresh(self) -> None:
        """Public method to refresh the tools cache."""
        await self._refresh_cache()

    async def get_tools(self, user_permissions: List[str] | None = None) -> List[ToolDefinition]:
        """
        Get available tools for a user.
        """
        if not settings.ENABLE_TOOLS:
            return []

        # Filter from cache
        if user_permissions:
            return [
                t for t in self._cache
                if not t.required_permissions or
                any(p in user_permissions for p in t.required_permissions)
            ]

        # Return only public tools
        return [t for t in self._cache if not t.required_permissions]

    async def get_all_tools(self) -> List[ToolDefinition]:
        """Get all enabled tools (for admin/debug)."""
        return self._cache.copy()

    async def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a specific tool by name from cache."""
        for tool in self._cache:
            if tool.name == name:
                return tool
        return None

    async def execute(
        self,
        tool_call: ToolCall,
        user_permissions: List[str] | None = None,
    ) -> ToolResult:
        """
        Execute a tool call.
        """
        # Get tool definition from cache
        tool_def = await self.get_tool(tool_call.name)
        if not tool_def:
            logger.warning(f"Tool not found: {tool_call.name}")
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                success=False,
                error=f"Tool '{tool_call.name}' not found",
            )

        return await self._executor.execute(tool_call, tool_def, user_permissions)

    @property
    def tool_count(self) -> int:
        """Number of cached tools."""
        return len(self._cache)

    @property
    def is_initialized(self) -> bool:
        """Whether service has been initialized."""
        return self._initialized

    async def close(self) -> None:
        """Cleanup resources."""
        await self._executor.close()

    # Admin methods for tool management

    async def create_tool(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        parameters: dict,
        is_builtin: bool = False,
        is_enabled: bool = True,
        endpoint: str | None = None,
        http_method: str = "POST",
        headers: dict | None = None,
        timeout: int = 30,
        required_permissions: List[str] | None = None,
    ) -> ToolDefinition:
        """Create a new tool and refresh cache."""
        tool = await self._repo.create(
            db=db,
            name=name,
            description=description,
            parameters=parameters,
            is_builtin=is_builtin,
            is_enabled=is_enabled,
            endpoint=endpoint,
            http_method=http_method,
            headers=headers,
            timeout=timeout,
            required_permissions=required_permissions,
        )
        # Don't refresh cache here - let caller commit first
        return ToolDefinition.from_db_model(tool)

    async def set_enabled(self, db: AsyncSession, tool_name: str, is_enabled: bool) -> bool:
        """Enable or disable a tool."""
        tool = await self._repo.get_by_name(db, tool_name)
        if not tool:
            return False
        await self._repo.set_enabled(db, tool.id, is_enabled)
        return True


# Singleton instance for the application
_tools_service: ToolsService | None = None


def get_tools_service() -> ToolsService | None:
    """Get the global tools service instance."""
    global _tools_service
    return _tools_service


async def initialize_tools_service(uow_factory: UnitOfWorkFactory) -> ToolsService:
    """Initialize the global tools service (call on startup)."""
    global _tools_service
    _tools_service = ToolsService(uow_factory)
    await _tools_service.initialize()
    return _tools_service
