import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query, Path
from app.dependencies.services import get_chat_service, get_session_service
from app.services.interfaces.chat import IChatService
from app.services.interfaces.session import ISessionService
from app.schemas.message import MessageCreate, ChatResponse, SessionHistory
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionInfo,
    SessionList,
)

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
        "- `Content` is the user's message.\n"
        "- `Session_id` provided, the message is added to the existing session, if not, a new session is created automatically.\n"
        "- `Thinking` activates the assistant's thinking, it may take longer to respond. Only works in some models.\n"
        "- `Stream` enables streaming responses."
    ),
    response_description="The user message and assistant response",
)
async def send_message(
    payload: MessageCreate,
    chat_service: IChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Send a message and get an AI response."""
    return await chat_service.send_message(payload)


@router.get(
    "/history/{session_id}",
    response_model=SessionHistory,
    status_code=status.HTTP_200_OK,
    summary="Get session history",
    description=(
        "**Get the full message history for a session.**\n\n"
        "Returns all messages in chronological order with session metadata."
    ),
    response_description="Session with message history",
)
async def get_session_history(
    session_id: UUID = Path(..., description="Session UUID"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of messages"),
    chat_service: IChatService = Depends(get_chat_service),
) -> SessionHistory:
    """Get message history for a session."""
    return await chat_service.get_session_history(session_id, limit)


# endregion CHAT


# region SESSIONS


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description=(
        "**Create a new empty chat session.**\n\n" "Useful for starting a conversation with a specific title."
    ),
    response_description="The created session",
)
async def create_session(
    payload: SessionCreate,
    session_service: ISessionService = Depends(get_session_service),
) -> SessionResponse:
    """Create a new chat session."""
    return await session_service.create(payload)


@router.get(
    "/sessions",
    response_model=SessionList,
    status_code=status.HTTP_200_OK,
    summary="List sessions",
    description=(
        "**Get a list of chat sessions with pagination.**\n\n" "Returns sessions ordered by most recent first."
    ),
    response_description="Paginated list of sessions",
)
async def list_sessions(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    session_service: ISessionService = Depends(get_session_service),
) -> SessionList:
    """List chat sessions with pagination."""
    sessions, total = await session_service.get_by_user(user_id, skip, limit)
    return SessionList(
        sessions=sessions,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get session",
    description="**Get a session by its ID.**",
    response_description="The requested session",
)
async def get_session(
    session_id: UUID = Path(..., description="Session UUID"),
    session_service: ISessionService = Depends(get_session_service),
) -> SessionResponse:
    """Get a session by ID."""
    return await session_service.get_by_id(session_id)


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update session",
    description="**Update a session's title.**",
    response_description="The updated session",
)
async def update_session(
    session_id: UUID = Path(..., description="Session UUID"),
    payload: SessionUpdate = ...,
    session_service: ISessionService = Depends(get_session_service),
) -> SessionResponse:
    """Update a session."""
    return await session_service.update(session_id, payload)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="**Delete a session and all its messages.**",
)
async def delete_session(
    session_id: UUID = Path(..., description="Session UUID"),
    session_service: ISessionService = Depends(get_session_service),
) -> None:
    """Delete a session."""
    await session_service.delete(session_id)


# endregion SESSIONS
