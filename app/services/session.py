import logging
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User
from app.repositories.interfaces.session import ISessionRepository
from app.repositories.interfaces.message import IMessageRepository
from app.services.interfaces.session import ISessionService
from app.db.unit_of_work import UnitOfWorkFactory
from app.schemas.session import SessionResponse, SessionInfo, SessionCreate, SessionUpdate
from app.models.session import Session
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class SessionService(ISessionService):
    """Service for session operations."""

    def __init__(
        self,
        session_repo: ISessionRepository,
        message_repo: IMessageRepository,
        uow_factory: UnitOfWorkFactory,
    ):
        self._session_repo = session_repo
        self._message_repo = message_repo
        self._uow_factory = uow_factory

    # region HELPERS

    async def _get_session_with_access_check(
        self,
        db: AsyncSession,
        session_id: UUID,
        user: Optional[User],
        action: str = "access",
    ) -> Session:
        """
        Get a session with ownership verification.

        Access rules:
        - Superuser: own sessions + anonymous sessions (not other users')
        - Regular user: own sessions only
        - No user: anonymous sessions only
        """
        session = await self._session_repo.get_by_id(db, session_id)

        if not session:
            raise NotFoundError(f"Session {session_id} not found")

        # Anonymous session
        if session.user_id is None:
            return session

        # Session has owner
        if user is None:
            logger.warning(f"Anonymous user tried to {action} session {session_id} owned by {session.user_id}")
            raise NotFoundError(f"Session {session_id} not found")

        # Check ownership
        if str(session.user_id) != str(user.sub):
            logger.warning(f"User {user.sub} tried to {action} session {session_id} owned by {session.user_id}")
            raise NotFoundError(f"Session {session_id} not found")

        return session

    def _to_response(self, session: Session) -> SessionResponse:
        """Convert session model to response schema."""
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    # endregion HELPERS

    # region CREATE

    async def create(self, payload: SessionCreate) -> SessionResponse:
        """Create a new session."""
        async with self._uow_factory() as db:

            logger.info(f"Creating session for user {payload.user_id}")

            session = await self._session_repo.create(
                db=db,
                user_id=payload.user_id,
                title=payload.title,
            )

            logger.info(f"Created session {session.id} for user {payload.user_id}")

            return self._to_response(session)

    # endregion CREATE

    # region READ

    async def get_by_id(self, session_id: UUID, user: Optional[User]) -> SessionInfo:
        """Get a session by ID with message count."""
        async with self._uow_factory() as db:

            logger.info(f"Getting session {session_id} for user {user.sub if user else 'anonymous'}")

            session = await self._get_session_with_access_check(db, session_id, user, "access")

            if not session:
                raise NotFoundError(f"Session {session_id} not found")

            message_count = await self._message_repo.count_by_session(db, session_id)

            logger.info(f"Retrieved session {session_id} for user {user.sub if user else 'anonymous'}")

            return SessionInfo(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                message_count=message_count,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )

    async def get_by_user(
        self,
        user: Optional[User],
        skip: int = 0,
        limit: int = 50,
        read_anonymous: bool = False,
    ) -> tuple[List[SessionInfo], int]:
        """Get sessions for a user with pagination."""
        async with self._uow_factory() as db:

            logger.info(f"Getting sessions for user {user.sub if user else 'anonymous'}")

            # If is superuser, allow both own and anonymous sessions
            if user and user.is_superuser:
                if read_anonymous:
                    sessions = await self._session_repo.get_by_superuser(db, user.sub, skip, limit)
                    total_user_sessions = await self._session_repo.count_by_user(db, user.sub)
                    total_anonymous_sessions = await self._session_repo.count_by_user(db, None)
                    total = total_user_sessions + total_anonymous_sessions
                if not read_anonymous:
                    sessions = await self._session_repo.get_by_user(db, user.sub, skip, limit)
                    total = await self._session_repo.count_by_user(db, user.sub)
            # If not superuser, only allow own sessions
            elif user is not None:
                user_id = user.sub if user else None
                sessions = await self._session_repo.get_by_user(db, user_id, skip, limit)
                total = await self._session_repo.count_by_user(db, user_id)
            # If no user, none sessions are allowed to be read
            else:
                sessions = []
                total = 0

            result = []
            for session in sessions:
                message_count = await self._message_repo.count_by_session(db, session.id)
                result.append(
                    SessionInfo(
                        id=session.id,
                        user_id=session.user_id,
                        title=session.title,
                        message_count=message_count,
                        created_at=session.created_at,
                        updated_at=session.updated_at,
                    )
                )

            logger.info(f"Retrieved {len(result)} sessions for user {user.sub if user else 'anonymous'}")

            return result, total

    # endregion READ

    # region UPDATE

    async def update(self, session_id: UUID, user: Optional[User], payload: SessionUpdate) -> SessionResponse:
        """Update a session."""
        async with self._uow_factory() as db:

            logger.info(f"Trying to update session {session_id}")

            # Verify access before updating
            session = await self._get_session_with_access_check(db, session_id, user, "update")

            if payload.title is not None:
                session = await self._session_repo.update_title(db, session_id, payload.title)

            logger.info(f"Updated session {session_id}")
            return self._to_response(session)

    # endregion UPDATE

    # region DELETE

    async def delete(self, session_id: UUID, user: Optional[User]) -> bool:
        """Delete a session."""
        async with self._uow_factory() as db:

            logger.info(f"Trying to delete session {session_id}")

            # Verify access before deleting
            await self._get_session_with_access_check(db, session_id, user, "delete")

            deleted = await self._session_repo.delete(db, session_id)
            if not deleted:
                raise NotFoundError(f"Session {session_id} not found")

            logger.info(f"Deleted session {session_id}")
            return True

    # endregion DELETE
