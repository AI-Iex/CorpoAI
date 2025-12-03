from fastapi import Depends

from app.repositories.session import SessionRepository
from app.repositories.message import MessageRepository

from app.repositories.interfaces.session import ISessionRepository
from app.repositories.interfaces.message import IMessageRepository

from app.services.session import SessionService
from app.services.chat import ChatService

from app.services.interfaces.session import ISessionService
from app.services.interfaces.chat import IChatService

from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager
from app.dependencies.llm import get_llm, get_context_manager

from app.db.unit_of_work import get_uow_factory, UnitOfWorkFactory


# region REPOSITORIES


def get_session_repository() -> ISessionRepository:
    """Get session repository instance."""
    return SessionRepository()


def get_message_repository() -> IMessageRepository:
    """Get message repository instance."""
    return MessageRepository()


# endregion REPOSITORIES


# region SERVICES


def get_session_service(
    session_repo: ISessionRepository = Depends(get_session_repository),
    message_repo: IMessageRepository = Depends(get_message_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> ISessionService:
    """Get session service instance."""
    return SessionService(
        session_repo=session_repo,
        message_repo=message_repo,
        uow_factory=uow_factory,
    )


def get_chat_service(
    session_repo: ISessionRepository = Depends(get_session_repository),
    message_repo: IMessageRepository = Depends(get_message_repository),
    llm_client: ILLMClient = Depends(get_llm),
    context_manager: IContextManager = Depends(get_context_manager),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IChatService:
    """Get chat service instance."""
    return ChatService(
        session_repo=session_repo,
        message_repo=message_repo,
        llm_client=llm_client,
        context_manager=context_manager,
        uow_factory=uow_factory,
    )


# endregion SERVICES
