import logging
import uuid
from pathlib import Path
from typing import Optional
import aiofiles
import aiofiles.os
from app.core.config import settings
from app.core.exceptions import DocumentUploadError
from app.services.interfaces.file_storage import IFileStorage

logger = logging.getLogger(__name__)


class LocalFileStorage(IFileStorage):
    """
    Local filesystem storage implementation.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize local file storage.
        """
        self._base_path = Path(base_path or settings.DOCUMENTS_STORAGE_PATH)
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"LocalFileStorage initialized at {self._base_path}")

    async def save(self, filename: str, content: bytes) -> str:
        """
        Save file to local filesystem.
        """
        # Generate unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = self._base_path / unique_filename

        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            logger.debug(f"File saved: {file_path}")
            return unique_filename

        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise DocumentUploadError(f"Failed to save file: {e}")

    async def read(self, path: str) -> bytes:
        """
        Read file from local filesystem.
        """
        file_path = self._base_path / path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """
        Delete file from local filesystem.
        """
        file_path = self._base_path / path

        try:
            if file_path.exists():
                await aiofiles.os.remove(file_path)
                logger.debug(f"File deleted: {file_path}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    async def exists(self, path: str) -> bool:
        """
        Check if file exists on local filesystem.
        """
        file_path = self._base_path / path
        return file_path.exists()

    def get_full_path(self, path: str) -> str:
        """
        Get full absolute path for a stored file.
        """
        return str(self._base_path / path)
