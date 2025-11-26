from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession


class IUnitOfWork(ABC):
    """
    Abstract base class for Unit of Work pattern.
    Defines the contract for transaction management.
    """

    @abstractmethod
    async def __aenter__(self) -> AsyncSession:
        """Enter async context manager, returning a database session."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager, handling commit/rollback."""
        ...

    @abstractmethod
    async def flush(self) -> None:
        """Flush pending changes without committing."""
        ...

    @abstractmethod
    async def refresh(self, instance) -> None:
        """Refresh an instance from the database."""
        ...
