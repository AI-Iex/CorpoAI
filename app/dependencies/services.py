from fastapi import Depends

from app.repositories.session import SessionRepository
from app.repositories.message import MessageRepository
from app.repositories.document import DocumentRepository
from app.repositories.vector_store import VectorStoreRepository

from app.repositories.interfaces.session import ISessionRepository
from app.repositories.interfaces.message import IMessageRepository
from app.repositories.interfaces.document import IDocumentRepository
from app.repositories.interfaces.vector_store import IVectorStoreRepository

from app.services.session import SessionService
from app.services.chat import ChatService
from app.services.document import DocumentService
from app.services.retrieval import RetrievalService
from app.services.chunking import ChunkingService
from app.services.file_storage import LocalFileStorage

from app.services.interfaces.session import ISessionService
from app.services.interfaces.chat import IChatService
from app.services.interfaces.document import IDocumentService
from app.services.interfaces.retrieval import IRetrievalService
from app.services.interfaces.chunking import IChunkingService
from app.services.interfaces.file_storage import IFileStorage

from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager
from app.clients.interfaces.embedding import IEmbeddingClient
from app.dependencies.llm import get_llm, get_context_manager
from app.dependencies.embedding import get_embedding

from app.db.unit_of_work import get_uow_factory, UnitOfWorkFactory
from app.core.config import settings


# region REPOSITORIES


def get_session_repository() -> ISessionRepository:
    """Get session repository instance."""
    return SessionRepository()


def get_message_repository() -> IMessageRepository:
    """Get message repository instance."""
    return MessageRepository()


def get_document_repository() -> IDocumentRepository:
    """Get document repository instance."""
    return DocumentRepository()


def get_vector_store_repository() -> IVectorStoreRepository:
    """Get vector store repository instance."""
    return VectorStoreRepository()


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


def get_chunking_service() -> IChunkingService:
    """Get chunking service instance."""
    return ChunkingService()


def get_file_storage() -> IFileStorage:
    """Get file storage instance."""
    return LocalFileStorage()


def get_retrieval_service(
    vector_store: IVectorStoreRepository = Depends(get_vector_store_repository),
) -> IRetrievalService:
    """Get retrieval service instance."""
    return RetrievalService(vector_store=vector_store)


def get_document_service(
    document_repo: IDocumentRepository = Depends(get_document_repository),
    vector_store: IVectorStoreRepository = Depends(get_vector_store_repository),
    chunking_service: IChunkingService = Depends(get_chunking_service),
    file_storage: IFileStorage = Depends(get_file_storage),
    embedding_client: IEmbeddingClient = Depends(get_embedding),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> IDocumentService:
    """Get document service instance."""
    return DocumentService(
        document_repo=document_repo,
        vector_store=vector_store,
        chunking_service=chunking_service,
        file_storage=file_storage,
        embedding_client=embedding_client,
        uow_factory=uow_factory,
    )


def get_optional_retrieval_service() -> IRetrievalService | None:
    """Get retrieval service if RAG is enabled, None otherwise."""
    if settings.ENABLE_RAG:
        return RetrievalService(vector_store=VectorStoreRepository())
    return None


def get_chat_service(
    session_repo: ISessionRepository = Depends(get_session_repository),
    message_repo: IMessageRepository = Depends(get_message_repository),
    llm_client: ILLMClient = Depends(get_llm),
    context_manager: IContextManager = Depends(get_context_manager),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
    retrieval_service: IRetrievalService | None = Depends(get_optional_retrieval_service),
) -> IChatService:
    """Get chat service instance."""
    return ChatService(
        session_repo=session_repo,
        message_repo=message_repo,
        llm_client=llm_client,
        context_manager=context_manager,
        uow_factory=uow_factory,
        retrieval_service=retrieval_service,
    )


# endregion SERVICES


# region FACTORIES (for use outside request context, e.g., background tasks)


def create_document_service() -> IDocumentService:
    """
    Create document service instance.
    """
    return DocumentService(
        document_repo=get_document_repository(),
        vector_store=get_vector_store_repository(),
        chunking_service=get_chunking_service(),
        file_storage=get_file_storage(),
        embedding_client=get_embedding(),
        uow_factory=get_uow_factory(),
    )


def create_retrieval_service() -> IRetrievalService:
    """
    Create retrieval service instance.
    """
    return RetrievalService(vector_store=get_vector_store_repository())


# endregion FACTORIES
