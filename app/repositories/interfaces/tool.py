from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool


class IToolRepository(ABC):
    """Interface for Tool repository operations."""

    # region CREATE

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        parameters: dict,
        is_builtin: bool = True,
        is_enabled: bool = True,
        endpoint: Optional[str] = None,
        http_method: str = "POST",
        headers: Optional[dict] = None,
        timeout: int = 30,
        required_permissions: Optional[List[str]] = None,
    ) -> Tool:
        """Create a new tool."""
        ...

    @abstractmethod
    async def upsert(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        parameters: dict,
        is_builtin: bool = True,
        is_enabled: bool = True,
        endpoint: Optional[str] = None,
        http_method: str = "POST",
        headers: Optional[dict] = None,
        timeout: int = 30,
        required_permissions: Optional[List[str]] = None,
    ) -> Tool:
        """Create or update a tool by name."""
        ...

    # endregion CREATE

    # region READ

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, tool_id: UUID) -> Optional[Tool]:
        """Get a tool by ID."""
        ...

    @abstractmethod
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        ...

    @abstractmethod
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_enabled: Optional[bool] = None,
        is_builtin: Optional[bool] = None,
    ) -> List[Tool]:
        """Get all tools with optional filters."""
        ...

    @abstractmethod
    async def get_enabled(self, db: AsyncSession) -> List[Tool]:
        """Get all enabled tools."""
        ...

    @abstractmethod
    async def get_for_user(
        self, db: AsyncSession, user_permissions: List[str]
    ) -> List[Tool]:
        """Get tools accessible to a user based on permissions."""
        ...

    @abstractmethod
    async def count(
        self,
        db: AsyncSession,
        is_enabled: Optional[bool] = None,
    ) -> int:
        """Count tools with optional filter."""
        ...

    # endregion READ

    # region UPDATE

    @abstractmethod
    async def update(
        self,
        db: AsyncSession,
        tool_id: UUID,
        **kwargs,
    ) -> Optional[Tool]:
        """Update a tool."""
        ...

    @abstractmethod
    async def set_enabled(
        self, db: AsyncSession, tool_id: UUID, is_enabled: bool
    ) -> Optional[Tool]:
        """Enable or disable a tool."""
        ...

    # endregion UPDATE

    # region DELETE

    @abstractmethod
    async def delete(self, db: AsyncSession, tool_id: UUID) -> bool:
        """Delete a tool."""
        ...

    # endregion DELETE
