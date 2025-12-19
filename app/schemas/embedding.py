from typing import List, Optional
from pydantic import BaseModel, Field


class EmbeddingVector(BaseModel):
    """Single embedding vector."""

    vector: List[float] = Field(..., description="Embedding vector values")
    dimension: int = Field(..., description="Vector dimension")

    @classmethod
    def from_list(cls, values: List[float]) -> "EmbeddingVector":
        """Create from list of floats."""
        return cls(vector=values, dimension=len(values))


class EmbeddingResult(BaseModel):
    """Result of embedding a single text."""

    text: str = Field(..., description="Original text")
    embedding: EmbeddingVector = Field(..., description="Embedding vector")
    model: Optional[str] = Field(None, description="Model used")


class EmbeddingBatchResult(BaseModel):
    """Result of embedding multiple texts (documents)."""

    embeddings: List[EmbeddingVector] = Field(..., description="List of embeddings")
    model: str = Field(..., description="Model used")
    dimension: int = Field(..., description="Vector dimension")
    count: int = Field(..., description="Number of embeddings")

    @classmethod
    def from_lists(
        cls,
        vectors: List[List[float]],
        model: str,
    ) -> "EmbeddingBatchResult":
        """Create from list of vector lists."""
        embeddings = [EmbeddingVector.from_list(v) for v in vectors]
        dimension = len(vectors[0]) if vectors else 0
        return cls(
            embeddings=embeddings,
            model=model,
            dimension=dimension,
            count=len(embeddings),
        )

    def to_lists(self) -> List[List[float]]:
        """Convert back to list of lists for ChromaDB compatibility."""
        return [e.vector for e in self.embeddings]


class QueryEmbeddingResult(BaseModel):
    """Result of embedding a query for search."""

    query: str = Field(..., description="Original query text")
    embedding: EmbeddingVector = Field(..., description="Query embedding vector")
    model: str = Field(..., description="Model used")

    def to_list(self) -> List[float]:
        """Convert to list for ChromaDB compatibility."""
        return self.embedding.vector
