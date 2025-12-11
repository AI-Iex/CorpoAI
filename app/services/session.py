import logging
from typing import Optional, List
from uuid import UUID
from app.repositories.interfaces.session import ISessionRepository
from app.repositories.interfaces.message import IMessageRepository
from app.services.interfaces.session import ISessionService
from app.db.unit_of_work import UnitOfWorkFactory
from app.schemas.session import SessionResponse, SessionInfo, SessionCreate, SessionUpdate
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

    # region CREATE

    async def create(self, payload: SessionCreate) -> SessionResponse:
        """Create a new session."""
        async with self._uow_factory() as db:
            session = await self._session_repo.create(
                db=db,
                user_id=payload.user_id,
                title=payload.title,
            )

            logger.info(f"Created session {session.id} for user {payload.user_id}")

            return SessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )

    # endregion CREATE

    # region READ

    async def get_by_id(self, session_id: UUID) -> SessionResponse:
        """Get a session by ID."""
        async with self._uow_factory() as db:
            session = await self._session_repo.get_by_id(db, session_id)

            if not session:
                raise NotFoundError(f"Session {session_id} not found")

            return SessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )

    async def get_by_user(
        self,
        user_id: Optional[UUID],
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[SessionInfo], int]:
        """Get sessions for a user with pagination."""
        async with self._uow_factory() as db:
            sessions = await self._session_repo.get_by_user(db, user_id, skip, limit)
            total = await self._session_repo.count_by_user(db, user_id)

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

            return result, total

    # endregion READ

    # region UPDATE

    async def update(self, session_id: UUID, payload: SessionUpdate) -> SessionResponse:
        """Update a session."""
        async with self._uow_factory() as db:
            session = await self._session_repo.get_by_id(db, session_id)

            if not session:
                raise NotFoundError(f"Session {session_id} not found")

            if payload.title is not None:
                session = await self._session_repo.update_title(db, session_id, payload.title)

            logger.info(f"Updated session {session_id}")

            return SessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )

    # endregion UPDATE

    # region DELETE

    async def delete(self, session_id: UUID) -> bool:
        """Delete a session."""
        async with self._uow_factory() as db:
            deleted = await self._session_repo.delete(db, session_id)

            if not deleted:
                raise NotFoundError(f"Session {session_id} not found")

            logger.info(f"Deleted session {session_id}")
            return True

    # endregion DELETE
