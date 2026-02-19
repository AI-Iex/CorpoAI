from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.tools import ToolsService, get_tools_service
from app.repositories.tool import ToolRepository
from app.db.unit_of_work import UnitOfWork
from app.schemas.tool import (
    ToolCreate,
    ToolUpdate,
    ToolSetEnabled,
    ToolResponse,
    ToolListResponse,
)
from app.core.config import settings

router = APIRouter(prefix="/tools", tags=["Tools"])

def _check_tools_enabled():
    """Check if tools feature is enabled."""
    if not settings.ENABLE_TOOLS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools feature is disabled",
        )


def _check_service(tools_service: ToolsService | None):
    """Check if tools service is initialized."""
    if not tools_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools service not initialized",
        )


# region LIST / GET


@router.get(
    "",
    response_model=ToolListResponse,
    summary="List all tools",
    description="Get paginated list of all tools (admin)",
)
async def list_tools(
    skip: int = 0,
    limit: int = 50,
    is_enabled: bool | None = None,
    is_builtin: bool | None = None,
    tools_service: ToolsService = Depends(get_tools_service),
) -> ToolListResponse:
    """
    List all tools with optional filters.

    - **skip**: Number of items to skip (pagination)
    - **limit**: Maximum items to return
    - **is_enabled**: Filter by enabled status
    - **is_builtin**: Filter by builtin status
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        tools = await repo.get_all(
            db, skip=skip, limit=limit, is_enabled=is_enabled, is_builtin=is_builtin
        )
        total = await repo.count(db, is_enabled=is_enabled)

    return ToolListResponse(
        tools=[ToolResponse.model_validate(t) for t in tools],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/enabled",
    response_model=List[dict],
    summary="List enabled tools",
    description="Get list of enabled tools for LLM (public)",
)
async def list_enabled_tools(
    tools_service: ToolsService = Depends(get_tools_service),
) -> List[dict]:
    """
    List enabled tools available for the AI assistant.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    tools = await tools_service.get_all_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.to_json_schema(),
        }
        for t in tools
    ]


@router.get(
    "/{tool_name}",
    response_model=ToolResponse,
    summary="Get tool details",
    description="Get details of a specific tool by name",
)
async def get_tool(
    tool_name: str,
    tools_service: ToolsService = Depends(get_tools_service),
) -> ToolResponse:
    """
    Get details of a specific tool by name.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        tool = await repo.get_by_name(db, tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    return ToolResponse.model_validate(tool)


# endregion LIST / GET

# region CREATE


@router.post(
    "",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tool",
    description="Create a new external tool definition",
)
async def create_tool(
    tool_data: ToolCreate,
    tools_service: ToolsService = Depends(get_tools_service),
) -> ToolResponse:
    """
    Create a new tool.

    External tools require an endpoint URL.
    Builtin tools should be added via seed script.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        # Check if tool already exists
        existing = await repo.get_by_name(db, tool_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tool '{tool_data.name}' already exists",
            )

        # Create tool
        tool = await repo.create(
            db=db,
            name=tool_data.name,
            description=tool_data.description,
            parameters=tool_data.parameters.model_dump(),
            is_builtin=tool_data.is_builtin,
            is_enabled=tool_data.is_enabled,
            endpoint=tool_data.endpoint,
            http_method=tool_data.http_method,
            headers=tool_data.headers,
            timeout=tool_data.timeout,
            required_permissions=tool_data.required_permissions,
        )
        await db.commit()

    # Refresh cache
    await tools_service.refresh()

    return ToolResponse.model_validate(tool)


# endregion CREATE

# region UPDATE


@router.patch(
    "/{tool_name}",
    response_model=ToolResponse,
    summary="Update a tool",
    description="Update an existing tool's configuration",
)
async def update_tool(
    tool_name: str,
    tool_data: ToolUpdate,
    tools_service: ToolsService = Depends(get_tools_service),
) -> ToolResponse:
    """
    Update a tool's configuration.

    Only provided fields will be updated.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        # Get existing tool
        existing = await repo.get_by_name(db, tool_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

        # Build update dict
        update_data = tool_data.model_dump(exclude_unset=True)
        if "parameters" in update_data and update_data["parameters"]:
            update_data["parameters"] = tool_data.parameters.model_dump()

        if not update_data:
            return ToolResponse.model_validate(existing)

        # Update tool
        tool = await repo.update(db, existing.id, **update_data)
        await db.commit()

    # Refresh cache
    await tools_service.refresh()

    return ToolResponse.model_validate(tool)


@router.patch(
    "/{tool_name}/enabled",
    response_model=ToolResponse,
    summary="Enable/disable a tool",
    description="Toggle a tool's enabled status",
)
async def set_tool_enabled(
    tool_name: str,
    data: ToolSetEnabled,
    tools_service: ToolsService = Depends(get_tools_service),
) -> ToolResponse:
    """
    Enable or disable a tool.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        existing = await repo.get_by_name(db, tool_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

        tool = await repo.set_enabled(db, existing.id, data.is_enabled)
        await db.commit()

    # Refresh cache
    await tools_service.refresh()

    return ToolResponse.model_validate(tool)


# endregion UPDATE

# region DELETE


@router.delete(
    "/{tool_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tool",
    description="Delete a tool definition (cannot delete builtin tools)",
)
async def delete_tool(
    tool_name: str,
    tools_service: ToolsService = Depends(get_tools_service),
):
    """
    Delete a tool.

    Builtin tools cannot be deleted.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    repo = ToolRepository()
    async with UnitOfWork() as db:
        existing = await repo.get_by_name(db, tool_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

        if existing.is_builtin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete builtin tools. Disable it instead.",
            )

        await repo.delete(db, existing.id)
        await db.commit()

    # Refresh cache
    await tools_service.refresh()


# endregion DELETE

# region ADMIN


@router.post(
    "/refresh",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Refresh tools cache",
    description="Force refresh of the in-memory tools cache",
)
async def refresh_tools_cache(
    tools_service: ToolsService = Depends(get_tools_service),
):
    """
    Force refresh of the tools cache from database.

    Use after direct database modifications.
    """
    _check_tools_enabled()
    _check_service(tools_service)

    await tools_service.refresh()


# endregion ADMIN
