import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Path
from app.dependencies.services import get_chat_service, get_session_service
from app.services.interfaces.chat import IChatService
from app.services.interfaces.session import ISessionService
from app.schemas.message import MessageCreate, MessageCreateInput, ChatResponse, SessionHistory
from app.schemas.session import (
    SessionBase,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionInfo,
    SessionList,
)
from app.schemas.user import User
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# region CHAT


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message",
    description=(
        "**Send a message to the AI assistant and receive a response.**\n\n"
        "If authenticated, the session is linked to the user. Otherwise, an anonymous session is created.\n\n"
        "- `content`: The user's message.\n"
        "- `session_id`: Optional. If provided, continues an existing session; otherwise creates a new one.\n"
        "- `thinking`: Activates extended reasoning (slower, model-dependent).\n"
        "- `stream`: Enables streaming responses."
    ),
    response_description="The user message and assistant response",
)
async def send_message(
    payload: MessageCreateInput,
    chat_service: IChatService = Depends(get_chat_service),
    user: Optional[User] = Depends(requires_permission(Permissions.CHAT_SENDMESSAGE)),
) -> ChatResponse:
    """Send a message and get an AI response."""

    if user:
        payload = MessageCreate(**payload.model_dump(), user_id=user.sub)
    else:
        payload = MessageCreate(**payload.model_dump())

    return await chat_service.send_message(payload)


@router.get(
    "/history/{session_id}",
    response_model=SessionHistory,
    status_code=status.HTTP_200_OK,
    summary="Get session history",
    description=(
        "**Get the full message history for a session.**\n\n"
        "**Access rules:**\n"
        "- Anonymous sessions: Accessible by anyone with the session ID.\n"
        "- User sessions: Only accessible by the session owner.\n\n"
        "- `session_id`: The unique identifier of the session.\n"
        "- `limit`: Optional limit on number of messages returned."
    ),
    response_description="Session with message history",
)
async def get_session_history(
    session_id: UUID = Path(..., description="Session UUID"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of messages"),
    chat_service: IChatService = Depends(get_chat_service),
    user: Optional[User] = Depends(requires_permission(Permissions.CHAT_READHISTORY)),
) -> SessionHistory:
    """Get message history for a session."""
    return await chat_service.get_session_history(session_id, user if user else None, limit)


# endregion CHAT


# region SESSIONS


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description=(
        "**Create a new empty chat session.**\n\n"
        "If authenticated, the session is linked to the user. Otherwise, an anonymous session is created.\n\n"
        "Anonymous sessions act as 'incognito mode' - only accessible via the session ID.\n\n"
        "- `title`: Name of the session."
    ),
    response_description="The created session",
)
async def create_session(
    payload: SessionBase,
    session_service: ISessionService = Depends(get_session_service),
    user: Optional[User] = Depends(requires_permission(Permissions.SESSIONS_CREATE)),
) -> SessionResponse:
    """Create a new chat session."""
    if user:
        payload = SessionCreate(**payload.model_dump(), user_id=user.sub)
    else:
        payload = SessionCreate(**payload.model_dump())
    return await session_service.create(payload)


@router.get(
    "/sessions",
    response_model=SessionList,
    status_code=status.HTTP_200_OK,
    summary="List sessions",
    description=(
        "**Get a list of chat sessions with pagination.**\n\n"
        "**Access rules:**\n"
        "- Unauthenticated users: Cannot list any sessions.\n"
        "- Regular users: Can only list their own sessions.\n"
        "- Superusers: Can list own sessions + anonymous sessions (with `read_anonymous=true`).\n\n"
        "- `read_anonymous`: Include anonymous sessions (superusers only).\n"
        "- `skip`: Number of sessions to skip.\n"
        "- `limit`: Maximum sessions to return (default: 50)."
    ),
    response_description="Paginated list of sessions",
)
async def list_sessions(
    read_anonymous: bool = Query(False, description="Filter to include anonymous sessions (superusers only)."),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    session_service: ISessionService = Depends(get_session_service),
    user: Optional[User] = Depends(requires_permission(Permissions.SESSIONS_READ)),
) -> SessionList:
    """List chat sessions with pagination."""
    sessions, total = await session_service.get_by_user(user if user else None, skip, limit, read_anonymous)
    return SessionList(
        sessions=sessions,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionInfo,
    status_code=status.HTTP_200_OK,
    summary="Get session",
    description=(
        "**Get a session by its ID.**\n\n"
        "**Access rules:**\n"
        "- Anonymous sessions: Accessible by anyone with the session ID.\n"
        "- User sessions: Only accessible by the session owner.\n\n"
        "- `session_id`: The unique identifier of the session."
    ),
    response_description="The requested session",
)
async def get_session(
    session_id: UUID = Path(..., description="Session UUID"),
    session_service: ISessionService = Depends(get_session_service),
    user: Optional[User] = Depends(requires_permission(Permissions.SESSIONS_READ)),
) -> SessionInfo:
    """Get a session by ID."""
    return await session_service.get_by_id(session_id, user if user else None)


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update session",
    description=(
        "**Update a session's title.**\n\n"
        "**Access rules:**\n"
        "- Anonymous sessions: Can be updated by anyone with the session ID.\n"
        "- User sessions: Only the session owner can update.\n\n"
        "- `session_id`: The unique identifier of the session."
    ),
    response_description="The updated session",
)
async def update_session(
    session_id: UUID = Path(..., description="Session UUID"),
    payload: SessionUpdate = ...,
    session_service: ISessionService = Depends(get_session_service),
    user: Optional[User] = Depends(requires_permission(Permissions.SESSIONS_UPDATE)),
) -> SessionResponse:
    """Update a session."""
    return await session_service.update(session_id, user if user else None, payload)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description=(
        "**Delete a session and all its messages.**\n\n"
        "**Access rules:**\n"
        "- Anonymous sessions: Can be deleted by anyone with the session ID.\n"
        "- User sessions: Only the session owner can delete.\n\n"
        "- `session_id`: The unique identifier of the session."
    ),
)
async def delete_session(
    session_id: UUID = Path(..., description="Session UUID"),
    session_service: ISessionService = Depends(get_session_service),
    user: Optional[User] = Depends(requires_permission(Permissions.SESSIONS_DELETE)),
) -> None:
    """Delete a session."""
    await session_service.delete(session_id, user if user else None)


# endregion SESSIONS
