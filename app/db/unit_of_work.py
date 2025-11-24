import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Unit of Work pattern for managing database transactions.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Unit of Work.
        """
        self.session = session
        self._committed = False

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type):
        """
        Exit async context manager.
        """
        if exc_type is not None:
            await self.rollback()
            return False

        if not self._committed:
            await self.commit()

        return True

    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        try:
            await self.session.commit()
            self._committed = True
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error("Failed to commit transaction")
            logger.debug(f"{e}")
            await self.rollback()
            raise DatabaseError("Failed to commit transaction")

    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        try:
            await self.session.rollback()
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error("Failed to rollback transaction")
            logger.debug(f"{e}")
            raise DatabaseError("Failed to rollback transaction")

    async def flush(self) -> None:
        """
        Flush pending changes without committing.
        """
        try:
            await self.session.flush()
            logger.debug("Session flushed successfully")
        except Exception as e:
            logger.error("Failed to flush session")
            logger.debug(f"{e}")
            raise DatabaseError("Failed to flush session")

    async def refresh(self, instance) -> None:
        """
        Refresh an instance from the database.
        """
        try:
            await self.session.refresh(instance)
            logger.debug(f"Instance {instance} refreshed successfully")
        except Exception as e:
            logger.error("Failed to refresh instance")
            logger.debug(f"{e}")
            raise DatabaseError("Failed to refresh instance")
