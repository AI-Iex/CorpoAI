from typing import Callable
from fastapi import Depends
from app.db.interfaces.unit_of_work import IUnitOfWork
from app.db.unit_of_work import UnitOfWorkFactory, get_uow_factory


def get_uow(
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IUnitOfWork:
    """
    Dependency for getting Unit of Work factory interface.
    """
    return uow_factory()
