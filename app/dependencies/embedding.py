from app.clients.embedding_client_manager import get_embedding_client
from app.clients.interfaces.embedding import IEmbeddingClient


def get_embedding() -> IEmbeddingClient:
    """
    Dependency to inject Embedding client into services.
    """
    return get_embedding_client()
