from typing import Callable
from chromadb import Client, Collection
from app.db.chroma_client import get_chroma_client, get_or_create_collection


def get_chroma() -> Client:
    """
    Dependency for getting ChromaDB client.
    """
    return get_chroma_client()


def get_collection_factory(collection_name: str) -> Callable[[], Collection]:
    """
    Dependency factory for getting a specific ChromaDB collection.
    """

    def _get_collection() -> Collection:
        return get_or_create_collection(collection_name)

    return _get_collection
