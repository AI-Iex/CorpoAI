import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.core.config import settings
from app.repositories.vector_store import VectorStoreRepository
from app.services.interfaces.retrieval import IRetrievalService
from app.clients.embedding_client_manager import get_embedding_client

logger = logging.getLogger(__name__)


class RetrievalService(IRetrievalService):
    """
    Service for semantic search and context retrieval.
    """

    def __init__(
        self,
        vector_store: VectorStoreRepository = None,
        top_k: int = None,
        min_relevance_score: float = None,
    ):
        """
        Initialize retrieval service.
        """
        self._vector_store = vector_store or VectorStoreRepository()
        self._top_k = top_k or settings.TOP_K_RETRIEVAL
        self._min_score = min_relevance_score or settings.MIN_RELEVANCE_SCORE

        logger.debug(
            "RetrievalService initialized",
            extra={"top_k": self._top_k, "min_score": self._min_score},
        )

    async def search(
        self,
        query: str,
        top_k: int = None,
        min_score: float = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        """
        top_k = top_k or self._top_k
        min_score = min_score or self._min_score

        try:
            # Generate query embedding
            embedding_client = get_embedding_client()
            query_result = await embedding_client.embed_query(query)

            # Build where filter if document IDs provided
            where_filter = None
            if document_ids:
                doc_ids_str = [str(doc_id) for doc_id in document_ids]
                where_filter = {"document_id": {"$in": doc_ids_str}}

            # Query vector store (returns raw ChromaDB results)
            raw_results = await self._vector_store.query(
                query_embedding=query_result.to_list(),
                n_results=top_k,
                where=where_filter,
            )

            # Convert raw results to structured format with scores
            search_results = self._process_query_results(raw_results, min_score)

            logger.debug(
                "Search completed",
                extra={
                    "query_preview": query[:50] + "..." if len(query) > 50 else query,
                    "total_results": len(raw_results.get("ids", [[]])[0]),
                    "filtered_results": len(search_results),
                },
            )

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _process_query_results(
        self,
        raw_results: Dict[str, Any],
        min_score: float,
    ) -> List[Dict[str, Any]]:
        """
        Process raw ChromaDB results into structured search results.
        Converts distances to similarity scores and filters by min_score.
        """
        search_results = []

        if not raw_results or not raw_results.get("ids") or not raw_results["ids"][0]:
            return search_results

        for i, chunk_id in enumerate(raw_results["ids"][0]):
            # ChromaDB returns distance, convert to similarity score
            # For cosine: similarity = 1 - distance
            distance = raw_results["distances"][0][i] if raw_results.get("distances") else 0
            score = 1 - distance

            # Filter by minimum score
            if score < min_score:
                continue

            search_results.append(
                {
                    "id": chunk_id,
                    "document": raw_results["documents"][0][i] if raw_results.get("documents") else "",
                    "metadata": raw_results["metadatas"][0][i] if raw_results.get("metadatas") else {},
                    "score": round(score, 4),
                }
            )

        return search_results

    async def get_context(
        self,
        query: str,
        max_tokens: int = 2000,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Get formatted context for LLM prompt.
        """
        # Estimate chars per token (rough approximation)
        max_chars = max_tokens * 4

        # Search for relevant chunks
        results = await self.search(query)

        if not results:
            return {
                "context": "",
                "sources": [],
                "has_context": False,
            }

        # Build context string
        context_parts = []
        sources = []
        current_length = 0

        for i, result in enumerate(results):
            chunk_text = result.get("document", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0)

            # Check if adding this chunk would exceed limit
            if current_length + len(chunk_text) > max_chars:
                # Try to fit partial content
                remaining = max_chars - current_length
                if remaining > 100:  # Only add if meaningful content
                    chunk_text = chunk_text[:remaining] + "..."
                else:
                    break

            # Format chunk with reference
            context_parts.append(f"[{i+1}] {chunk_text}")
            current_length += len(chunk_text)

            # Track source (align with SourceReference schema)
            if include_sources:
                doc_id = metadata.get("document_id")
                source_info = {
                    "document_id": doc_id if doc_id else "00000000-0000-0000-0000-000000000000",
                    "document_name": metadata.get("filename", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "score": round(score, 4),
                    "text_preview": chunk_text[:150] + "..." if len(chunk_text) > 150 else chunk_text,
                }
                sources.append(source_info)

        context = "\n\n".join(context_parts)

        logger.debug(
            "Context built",
            extra={
                "chunks_used": len(context_parts),
                "context_length": len(context),
                "sources_count": len(sources),
            },
        )

        return {
            "context": context,
            "sources": sources,
            "has_context": bool(context),
        }

    async def get_context_for_prompt(
        self,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Get context formatted for direct inclusion in LLM prompt.
        Simpler version that returns just the context string.
        """
        result = await self.get_context(query, max_tokens, include_sources=True)

        if not result["has_context"]:
            return ""

        # Format with header and sources
        context_text = result["context"]
        sources = result["sources"]

        # Build source references
        if sources:
            source_refs = ", ".join([f"[{s['index']}] {s['filename']}" for s in sources])
            footer = f"\n\nSources: {source_refs}"
        else:
            footer = ""

        return f"Relevant context from corporate documents:\n\n{context_text}{footer}"
