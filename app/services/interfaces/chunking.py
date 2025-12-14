from abc import ABC, abstractmethod
from typing import List, Tuple

from app.schemas.document import DocumentMetadata, TextChunk


class IChunkingService(ABC):
    """Interface for text extraction and chunking service."""

    @abstractmethod
    async def extract_text(self, file_path: str) -> Tuple[str, DocumentMetadata]:
        """
        Extract text from a file based on its type.
        """
        pass

    @abstractmethod
    async def split_text(
        self,
        text: str,
        metadata: DocumentMetadata = None,
    ) -> List[TextChunk]:
        """
        Split text into chunks with metadata.
        """
        pass

    @abstractmethod
    async def process_file(
        self,
        file_path: str,
    ) -> Tuple[List[TextChunk], DocumentMetadata]:
        """
        Extract text from file and split into chunks.
        """
        pass

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        """Get configured chunk size."""
        pass

    @property
    @abstractmethod
    def chunk_overlap(self) -> int:
        """Get configured chunk overlap."""
        pass
