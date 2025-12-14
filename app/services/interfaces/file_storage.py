from abc import ABC, abstractmethod
from typing import Optional


class IFileStorage(ABC):
    """
    Interface for file storage operations.
    """

    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """
        Save file content to storage.
        """
        pass

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """
        Read file content from storage.
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        Delete file from storage.
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if file exists in storage.
        """
        pass

    @abstractmethod
    def get_full_path(self, path: str) -> str:
        """
        Get the full path/URL for a stored file.
        """
        pass
