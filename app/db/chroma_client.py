import logging
from typing import Optional
import chromadb
from chromadb import Client, Collection, HttpClient, PersistentClient
from chromadb.config import Settings as ChromaSettings
from app.core.enums import ChromaMode
from app.core.config import settings
from app.core.exceptions import ValidationError, VectorStoreError

logger = logging.getLogger(__name__)

# Global ChromaDB client instance
_chroma_client: Optional[Client] = None


def get_chroma_client() -> Client:
    """
    Get or create ChromaDB client singleton.

    Supports two modes:
    - local: PersistentClient (embedded)
    - server: HttpClient (client-server)

    Mode is controlled by CHROMA_MODE environment variable.
    """
    global _chroma_client

    if _chroma_client is None:
        try:

            chroma_mode = settings.CHROMA_MODE.lower()
            logger.debug(f"ChromaDB mode: {chroma_mode}")

            # Server
            if chroma_mode == ChromaMode.SERVER:

                logger.debug(f"Initializing ChromaDB HttpClient at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
                _chroma_client = HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                logger.debug("ChromaDB HttpClient initialized successfully")

            # Local
            elif chroma_mode == ChromaMode.LOCAL:

                logger.debug(f"Initializing ChromaDB PersistentClient at {settings.CHROMA_PERSIST_DIRECTORY}")
                _chroma_client = PersistentClient(
                    path=settings.CHROMA_PERSIST_DIRECTORY,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True,  # Only for development
                    ),
                )
                logger.debug("ChromaDB PersistentClient initialized successfully")

            else:
                raise ValidationError(f"Invalid CHROMA_MODE: {chroma_mode}")

        except ValidationError:
            raise
        except Exception as e:
            logger.error("Failed to initialize ChromaDB client")
            logger.debug(f"Err msg: {e}", exc_info=True)
            raise VectorStoreError("ChromaDB initialization failed") from e

    return _chroma_client


def get_or_create_collection(
    collection_name: str,
    client: Optional[Client] = None,
    metadata: Optional[dict] = None,
) -> Collection:
    """
    Get or create a ChromaDB collection.
    """
    if client is None:
        client = get_chroma_client()

    if metadata is None:
        metadata = {"description": f"Collection: {collection_name}"}

    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
        )
        logger.debug(f"Collection '{collection_name}' ready")
        return collection

    except Exception as e:
        logger.error(f"Failed to get/create collection '{collection_name}'")
        logger.debug(f"Err msg: {e}", exc_info=True)
        raise


async def init_chroma() -> None:
    """
    Initialize ChromaDB client and test connection.
    """
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        collection_count = len(collections)

        chroma_mode = settings.CHROMA_MODE.lower()
        logger.debug(f"ChromaDB ({chroma_mode} mode) initialized successfully. Collections: {collection_count}")

    except Exception as e:
        logger.error("Failed to initialize ChromaDB")
        logger.debug(f"Err msg: {e}", exc_info=True)
        raise


async def close_chroma() -> None:
    """
    Close ChromaDB client.
    """
    global _chroma_client

    if _chroma_client is not None:
        logger.debug("ChromaDB client cleanup")
        _chroma_client = None
