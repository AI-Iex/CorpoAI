import logging
from typing import Optional
from app.core.config import settings
from app.clients.interfaces.embedding import IEmbeddingClient
from app.clients.embedding.sentence_transformer import SentenceTransformerClient

logger = logging.getLogger(__name__)

_embedding_client: Optional[IEmbeddingClient] = None


def init_embedding_client() -> IEmbeddingClient:
    """
    Initialize embedding client based on configuration.
    """
    global _embedding_client

    if _embedding_client is not None:
        logger.warning("Embedding client already initialized, returning existing instance")
        return _embedding_client

    logger.debug(
        "Initializing embedding client",
        extra={
            "model": settings.EMBEDDING_MODEL,
            "device": settings.EMBEDDING_DEVICE,
            "dimension": settings.EMBEDDING_DIMENSION,
        },
    )

    _embedding_client = SentenceTransformerClient(
        model_name=settings.EMBEDDING_MODEL,
        device=settings.EMBEDDING_DEVICE,
        batch_size=settings.BATCH_SIZE,
    )

    logger.debug("Embedding client initialized successfully", extra={"model": settings.EMBEDDING_MODEL})

    return _embedding_client


def get_embedding_client() -> IEmbeddingClient:
    """
    Get the embedding client instance.
    """
    if _embedding_client is None:
        raise RuntimeError("Embedding client not initialized. Call init_embedding_client() first.")
    return _embedding_client


def close_embedding_client() -> None:
    """
    Close and cleanup embedding client resources.
    """
    global _embedding_client

    if _embedding_client is not None:
        logger.debug("Closing embedding client")
        if hasattr(_embedding_client, "close"):
            _embedding_client.close()
        _embedding_client = None
        logger.debug("Embedding client closed successfully")
    else:
        logger.warning("Embedding client already closed or never initialized")
