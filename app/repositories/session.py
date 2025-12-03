import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.session import Session as SessionModel
from app.repositories.interfaces.session import ISessionRepository
from app.core.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class SessionRepository(ISessionRepository):
    """Repository for session CRUD operations."""

    # region CREATE

    async def create(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        title: str,
    ) -> SessionModel:
        """Create a new session."""
        try:
            session = SessionModel(
                user_id=user_id,
                title=title,
            )
            db.add(session)
            await db.flush()
            await db.refresh(session)

            return session

        except IntegrityError as e:
            raise RepositoryError("Failed to create session: integrity error") from e

        except Exception as e:
            raise RepositoryError(f"Failed to create session: {e}") from e

    # endregion CREATE

    # region READ

    async def get_by_id(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> Optional[SessionModel]:
        """Get a session by ID."""
        try:
            result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
            return result.scalar_one_or_none()

        except Exception as e:
            raise RepositoryError(f"Failed to get session: {e}") from e

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        skip: int = 0,
        limit: int = 50,
    ) -> List[SessionModel]:
        """Get sessions for a user with pagination, ordered by most recent first."""
        try:
            query = (
                select(SessionModel)
                .where(SessionModel.user_id == user_id)
                .order_by(SessionModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(f"Failed to get sessions: {e}") from e

    async def count_by_user(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
    ) -> int:
        """Count total sessions for a user."""
        try:
            result = await db.execute(select(func.count(SessionModel.id)).where(SessionModel.user_id == user_id))
            return result.scalar_one()

        except Exception as e:
            raise RepositoryError(f"Failed to count sessions: {e}") from e

    # endregion READ

    # region UPDATE

    async def update_title(
        self,
        db: AsyncSession,
        session_id: UUID,
        title: str,
    ) -> Optional[SessionModel]:
        """Update session title."""
        try:
            session = await self.get_by_id(db, session_id)
            if not session:
                return None

            session.title = title
            await db.flush()
            await db.refresh(session)

            return session

        except Exception as e:
            raise RepositoryError(f"Failed to update session: {e}") from e

    async def update_summary(
        self,
        db: AsyncSession,
        session_id: UUID,
        summary: str,
        summary_up_to_message_id: UUID,
    ) -> Optional[SessionModel]:
        """Update session summary and the last summarized message ID."""
        try:
            session = await self.get_by_id(db, session_id)
            if not session:
                return None

            session.summary = summary
            session.summary_up_to_message_id = summary_up_to_message_id
            await db.flush()
            await db.refresh(session)

            return session

        except Exception as e:
            raise RepositoryError(f"Failed to update session summary: {e}") from e

    # endregion UPDATE

    # region DELETE

    async def delete(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> bool:
        """Delete a session by ID. Messages are deleted via CASCADE."""
        try:
            result = await db.execute(delete(SessionModel).where(SessionModel.id == session_id))
            deleted = result.rowcount > 0

            return deleted

        except Exception as e:
            raise RepositoryError(f"Failed to delete session: {e}") from e

    # endregion DELETE
