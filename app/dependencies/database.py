from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork


async def get_uow(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency for getting Unit of Work instance.
    """
    async with UnitOfWork(session) as uow:
        yield uow
