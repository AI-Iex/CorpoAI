import logging
import time
from typing import Optional, List
from uuid import UUID
from app.schemas.user import User
from app.repositories.interfaces.session import ISessionRepository
from app.repositories.interfaces.message import IMessageRepository
from app.services.interfaces.chat import IChatService
from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager
from app.db.unit_of_work import UnitOfWorkFactory
from app.schemas.message import (
    MessageCreate,
    ChatResponse,
    SessionHistory,
    UserMessageResponse,
    AssistantMessageResponse,
)
from app.models.session import Session
from app.models.message import Message
from app.core.enums import MessageRoleTypes
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

DEFAULT_SESSION_TITLE = "New Chat"


class ChatService(IChatService):
    """Service for chat operations with LLM integration."""

    def __init__(
        self,
        session_repo: ISessionRepository,
        message_repo: IMessageRepository,
        llm_client: ILLMClient,
        context_manager: IContextManager,
        uow_factory: UnitOfWorkFactory,
    ):
        self._sessions = session_repo
        self._messages = message_repo
        self._llm = llm_client
        self._context = context_manager
        self._uow = uow_factory

    # region SEND MESSAGE

    async def send_message(self, payload: MessageCreate) -> ChatResponse:
        """Send a message and get AI response."""
        start = time.perf_counter()

        async with self._uow() as db:

            logger.info(f"Sending message in session {payload.session_id if payload.session_id else 'new session'}")

            # Get or create session
            session = await self._get_or_create_session(db, payload)

            # Save user message to DB
            user_msg = await self._messages.create(db, session.id, MessageRoleTypes.USER, payload.content)

            # Get history of the session
            all_msgs = await self._messages.get_by_session(db, session.id)

            # Determine unsummarized messages
            unsummarized = self._context.extract_unsummarized(all_msgs, session.summary_up_to_message_id)

            # Build context
            context = await self._context.build_context(unsummarized, payload.content, session.summary)

            # Update summary if needed
            if context.needs_summary_update:
                await self._sessions.update_summary(
                    db, session.id, context.new_summary, context.summary_up_to_message_id
                )

            # Get LLM response
            response = await self._llm.chat(context.messages, thinking=payload.thinking)

            # Save assistant message
            latency = (time.perf_counter() - start) * 1000
            assistant_msg = await self._messages.create(
                db,
                session.id,
                MessageRoleTypes.ASSISTANT,
                response.content,
                tokens_used=response.tokens_used,
                latency_ms=latency,
            )

            # Auto-title new sessions
            if await self._messages.count_by_session(db, session.id) == 2:
                title = payload.content[:50].strip() + ("..." if len(payload.content) > 50 else "")
                await self._sessions.update_title(db, session.id, title)

            logger.info(f"Chat: session={session.id}, latency={latency:.0f}ms, tokens={response.tokens_used}")

            return ChatResponse(
                session_id=session.id,
                user_message=self._to_response(user_msg),
                assistant_message=self._to_response(assistant_msg),
            )

    async def _get_or_create_session(self, db, payload: MessageCreate) -> Session:
        """Get existing session or create new one."""

        # If session is provided by the client, check if exists and return it
        if payload.session_id:
            session = await self._sessions.get_by_id(db, payload.session_id)
            if not session:
                raise NotFoundError(f"Session {payload.session_id} not found")
            return session

        # Session not provided, create a new one
        session = await self._sessions.create(db, payload.user_id, DEFAULT_SESSION_TITLE)
        logger.info(f"New session created: {session.id}")
        return session

    # endregion SEND MESSAGE

    # region GET HISTORY

    async def get_session_history(
        self, session_id: UUID, user: Optional[User] = None, limit: Optional[int] = None
    ) -> SessionHistory:
        """
        Get message history for a session.\n
        If user is provided, ensure the session belongs to the user, if not provided, ensure session is anonymous\n
        If the user is a superuser, allow access to both own and anonymous sessions.
        """
        async with self._uow() as db:

            logger.info(
                f"Getting session history for session {session_id} and user {user.sub if user else 'anonymous'}"
            )

            # If user is authenticated, check session ownership
            if user is not None:
                # If superuser, allow access to his own and anonymous sessions
                if user.is_superuser:
                    session = await self._sessions.get_by_id(db, session_id)
                    # Superuser can access: own sessions + anonymous sessions
                    # Cannot access: other users' sessions
                    if session and session.user_id is not None and str(session.user_id) != str(user.sub):
                        logger.warning(f"Unauthorized access attempt to session {session_id} by superuser {user.sub}")
                        raise NotFoundError(f"Session {session_id} not found")
                # If regular user, restrict to own sessions only
                else:
                    session = await self._sessions.get_by_id_and_user(db, session_id, user.sub)
                    # get_by_id_and_user already filters by user_id, so if session is None, it means not found or not owned
                    if not session:
                        logger.warning(f"Unauthorized access attempt to session {session_id} by user {user.sub}")
                        raise NotFoundError(f"Session {session_id} not found")
            # If no user, only allow anonymous sessions
            else:
                session = await self._sessions.get_by_id(db, session_id)
                # If session exists but belongs to a user, raise not found
                if session and session.user_id is not None:
                    logger.warning(f"Unauthorized access attempt to session {session_id} by anonymous user")
                    raise NotFoundError(f"Session {session_id} not found")

            if not session:
                raise NotFoundError(f"Session {session_id} not found")

            logger.info(
                f"Retrieved session history for session {session_id} and user {user.sub if user else 'anonymous'}"
            )

            return SessionHistory(
                session_id=session.id,
                title=session.title,
                message_count=await self._messages.count_by_session(db, session_id),
                messages=await self.get_messages(session_id, limit),
                created_at=session.created_at,
                updated_at=session.updated_at,
            )

    async def get_messages(
        self, session_id: UUID, limit: Optional[int] = None
    ) -> List[UserMessageResponse | AssistantMessageResponse]:
        """Get messages for a session."""
        async with self._uow() as db:
            messages = await self._messages.get_by_session(db, session_id, limit)
            return [self._to_response(m) for m in messages]

    # endregion GET HISTORY

    # region HELPERS

    def _to_response(self, msg: Message) -> UserMessageResponse | AssistantMessageResponse:
        """Convert message model to response schema."""
        common = {
            "message_id": msg.id,
            "session_id": msg.session_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at,
        }
        if msg.role == MessageRoleTypes.USER:
            return UserMessageResponse(**common)
        return AssistantMessageResponse(
            **common,
            sources=msg.sources,
            tool_calls=msg.tool_calls,
            tokens_used=msg.tokens_used,
            latency_ms=msg.latency_ms,
        )

    # endregion HELPERS
