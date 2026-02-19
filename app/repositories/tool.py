import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, delete, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.models.tool import Tool
from app.repositories.interfaces.tool import IToolRepository
from app.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class ToolRepository(IToolRepository):
    """Repository for Tool CRUD operations."""

    # region CREATE

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
        try:
            tool = Tool(
                name=name,
                description=description,
                parameters=parameters,
                is_builtin=is_builtin,
                is_enabled=is_enabled,
                endpoint=endpoint,
                http_method=http_method,
                headers=headers,
                timeout=timeout,
                required_permissions=required_permissions or [],
            )
            db.add(tool)
            await db.flush()
            await db.refresh(tool)
            return tool

        except IntegrityError as e:
            raise RepositoryError(f"Tool with name '{name}' already exists") from e
        except Exception as e:
            raise RepositoryError(f"Failed to create tool: {e}") from e

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
        try:
            stmt = insert(Tool).values(
                name=name,
                description=description,
                parameters=parameters,
                is_builtin=is_builtin,
                is_enabled=is_enabled,
                endpoint=endpoint,
                http_method=http_method,
                headers=headers,
                timeout=timeout,
                required_permissions=required_permissions or [],
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=["name"],
                set_={
                    "description": description,
                    "parameters": parameters,
                    "is_builtin": is_builtin,
                    "endpoint": endpoint,
                    "http_method": http_method,
                    "headers": headers,
                    "timeout": timeout,
                    "required_permissions": required_permissions or [],
                    # Note: is_enabled is NOT updated to preserve admin settings
                },
            )

            await db.execute(stmt)
            await db.flush()

            # Fetch the upserted tool
            return await self.get_by_name(db, name)

        except Exception as e:
            raise RepositoryError(f"Failed to upsert tool: {e}") from e

    # endregion CREATE

    # region READ

    async def get_by_id(self, db: AsyncSession, tool_id: UUID) -> Optional[Tool]:
        """Get a tool by ID."""
        try:
            query = select(Tool).where(Tool.id == tool_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to get tool: {e}") from e

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        try:
            query = select(Tool).where(Tool.name == name)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to get tool by name: {e}") from e

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_enabled: Optional[bool] = None,
        is_builtin: Optional[bool] = None,
    ) -> List[Tool]:
        """Get all tools with optional filters."""
        try:
            query = select(Tool)

            if is_enabled is not None:
                query = query.where(Tool.is_enabled == is_enabled)
            if is_builtin is not None:
                query = query.where(Tool.is_builtin == is_builtin)

            query = query.order_by(Tool.name)
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get tools: {e}") from e

    async def get_enabled(self, db: AsyncSession) -> List[Tool]:
        """Get all enabled tools."""
        return await self.get_all(db, is_enabled=True, limit=1000)

    async def get_for_user(
        self, db: AsyncSession, user_permissions: List[str]
    ) -> List[Tool]:
        """Get tools accessible to a user based on permissions.
        
        A tool is accessible if:
        - It has no required permissions (public), OR
        - User has at least one of the required permissions
        """
        try:
            query = select(Tool).where(Tool.is_enabled == True)  # noqa: E712

            # Filter by permissions
            # Tool is accessible if required_permissions is empty or user has any of them
            if user_permissions:
                query = query.where(
                    or_(
                        Tool.required_permissions == [],
                        Tool.required_permissions.op("?|")(user_permissions),
                    )
                )
            else:
                # No permissions - only public tools
                query = query.where(Tool.required_permissions == [])

            query = query.order_by(Tool.name)
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get tools for user: {e}") from e

    async def count(
        self,
        db: AsyncSession,
        is_enabled: Optional[bool] = None,
        is_builtin: Optional[bool] = None,
    ) -> int:
        """Count tools with optional filters."""
        try:
            query = select(func.count(Tool.id))
            if is_enabled is not None:
                query = query.where(Tool.is_enabled == is_enabled)
            if is_builtin is not None:
                query = query.where(Tool.is_builtin == is_builtin)
            result = await db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            raise RepositoryError(f"Failed to count tools: {e}") from e

    # endregion READ

    # region UPDATE

    async def update(
        self,
        db: AsyncSession,
        tool_id: UUID,
        **kwargs,
    ) -> Optional[Tool]:
        """Update a tool."""
        try:
            # Filter out None values and invalid fields
            valid_fields = {
                "name", "description", "parameters", "is_builtin",
                "is_enabled", "endpoint", "http_method", "headers",
                "timeout", "required_permissions"
            }
            updates = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}

            if not updates:
                return await self.get_by_id(db, tool_id)

            stmt = (
                update(Tool)
                .where(Tool.id == tool_id)
                .values(**updates)
                .returning(Tool)
            )
            result = await db.execute(stmt)
            await db.flush()
            return result.scalar_one_or_none()

        except IntegrityError as e:
            raise RepositoryError("Tool name already exists") from e
        except Exception as e:
            raise RepositoryError(f"Failed to update tool: {e}") from e

    async def set_enabled(
        self, db: AsyncSession, tool_id: UUID, is_enabled: bool
    ) -> Optional[Tool]:
        """Enable or disable a tool."""
        return await self.update(db, tool_id, is_enabled=is_enabled)

    # endregion UPDATE

    # region DELETE

    async def delete(self, db: AsyncSession, tool_id: UUID) -> bool:
        """Delete a tool."""
        try:
            stmt = delete(Tool).where(Tool.id == tool_id)
            result = await db.execute(stmt)
            await db.flush()
            return result.rowcount > 0
        except Exception as e:
            raise RepositoryError(f"Failed to delete tool: {e}") from e

    # endregion DELETE
