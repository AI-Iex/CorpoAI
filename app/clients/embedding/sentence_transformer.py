import logging
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from app.clients.interfaces.embedding import IEmbeddingClient
from app.schemas.embedding import (
    EmbeddingBatchResult,
    EmbeddingVector,
    QueryEmbeddingResult,
)

logger = logging.getLogger(__name__)


class SentenceTransformerClient(IEmbeddingClient):
    """
    Embedding client using sentence-transformers library.
    """

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        """Initialize the sentence-transformers client."""
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model: SentenceTransformer | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._dimension: int | None = None

    # region PROPERTIES

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            model = self._load_model()
            self._dimension = model.get_sentence_embedding_dimension()
        return self._dimension

    # endregion PROPERTIES

    # region PRIVATE METHODS

    def _load_model(self) -> SentenceTransformer:
        """
        Lazy load the model.
        """

        if self._model is None:
            logger.info(f"Loading embedding model: {self._model_name} on {self._device}")
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Dimension: {self._dimension}")
        return self._model

    def _prepare_document(self, text: str) -> str:
        """
        Prepare text as document/passage (E5 format).
        """

        if not text.startswith(("query:", "passage:")):
            return f"passage: {text}"
        return text

    def _prepare_query(self, text: str) -> str:
        """
        Prepare text as query (E5 format).
        """

        if not text.startswith(("query:", "passage:")):
            return f"query: {text}"
        return text

    def _encode_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous encoding.
        """
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    # endregion PRIVATE METHODS

    # region PUBLIC METHODS

    async def embed_documents(self, texts: List[str]) -> EmbeddingBatchResult:
        """
        Generate embeddings for documents.
        """

        if not texts:
            return EmbeddingBatchResult(
                embeddings=[],
                model=self._model_name,
                dimension=self.dimension,
                count=0,
            )

        prepared_texts = [self._prepare_document(t) for t in texts]
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            self._executor,
            self._encode_sync,
            prepared_texts,
        )

        logger.debug(f"Generated {len(vectors)} document embeddings")

        return EmbeddingBatchResult.from_lists(
            vectors=vectors,
            model=self._model_name,
        )

    async def embed_query(self, text: str) -> QueryEmbeddingResult:
        """
        Generate embedding for a search query.
        """

        prepared_text = self._prepare_query(text)

        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            self._executor,
            self._encode_sync,
            [prepared_text],
        )

        logger.debug("Generated query embedding")

        return QueryEmbeddingResult(
            query=text,
            embedding=EmbeddingVector.from_list(vectors[0]),
            model=self._model_name,
        )

    async def check_health(self) -> bool:
        """
        Check if model can be loaded and generate embeddings.
        """

        try:
            result = await self.embed_query("health check")
            return result.embedding.dimension == self.dimension
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            return False

    def close(self) -> None:
        """
        Cleanup resources.
        """

        self._executor.shutdown(wait=True)
        self._model = None
        self._dimension = None
        logger.info("SentenceTransformerClient closed")

    # endregion PUBLIC METHODS
