import logging
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DatabaseError
from app.db.session import AsyncSessionLocal
from app.db.interfaces.unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


class UnitOfWork(IUnitOfWork):
    """
    Unit of Work pattern for managing database transactions.
    Automatically creates, commits/rollbacks, and closes the session.
    """

    def __init__(self):
        """Initialize Unit of Work."""
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        """
        Enter async context manager, creating a new session.
        Returns the session for direct use.
        """
        self._session = AsyncSessionLocal()
        logger.debug("UnitOfWork: Session created")
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context manager.
        Commits if no exception, rolls back if exception occurred.
        Always closes the session.
        """
        if not self._session:
            return

        try:
            if exc_type is not None:
                await self._session.rollback()
                logger.debug(f"UnitOfWork: Transaction rolled back due to {exc_type.__name__}")
            else:
                await self._session.commit()
                logger.debug("UnitOfWork: Transaction committed successfully")
        except Exception as e:
            logger.error("UnitOfWork: Failed to commit/rollback transaction")
            logger.debug(f"Err msg: {e}", exc_info=True)
            try:
                await self._session.rollback()
            except Exception:
                pass
            raise DatabaseError("Failed to complete transaction") from e
        finally:
            await self._session.close()
            logger.debug("UnitOfWork: Session closed")
            self._session = None

    async def flush(self) -> None:
        """
        Flush pending changes without committing.
        Useful for getting auto-generated IDs before commit.
        """
        if not self._session:
            raise DatabaseError("No active session")
        
        try:
            await self._session.flush()
            logger.debug("UnitOfWork: Session flushed successfully")
        except Exception as e:
            logger.error("UnitOfWork: Failed to flush session")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise DatabaseError("Failed to flush session") from e

    async def refresh(self, instance) -> None:
        """
        Refresh an instance from the database.
        Reloads the object's state from the database.
        """
        if not self._session:
            raise DatabaseError("No active session")
        
        try:
            await self._session.refresh(instance)
            logger.debug(f"UnitOfWork: Instance {type(instance).__name__} refreshed")
        except Exception as e:
            logger.error("UnitOfWork: Failed to refresh instance")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise DatabaseError("Failed to refresh instance") from e

UnitOfWorkFactory = Callable[[], IUnitOfWork]


def get_uow_factory() -> UnitOfWorkFactory:
    """
    Factory function for dependency injection.
    Returns a callable that creates new UnitOfWork instances.
    """
    return UnitOfWork
