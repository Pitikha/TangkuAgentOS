"""
AI Foundation Framework - Embedding Models

This module defines embedding-related models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EmbeddingResult:
    """
    Result from an embedding operation.
    
    Attributes:
        text: The original text that was embedded.
        embedding: The embedding vector.
        model: Model used for embedding.
        provider: Provider used for embedding.
        dimensions: Number of dimensions in the embedding.
        token_count: Number of tokens in the text.
        timestamp: When the embedding was created.
        metadata: Additional metadata.
    """

    text: str
    embedding: List[float]
    model: str = ""
    provider: str = ""
    dimensions: int = 0
    token_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def vector(self) -> List[float]:
        """Get the embedding vector."""
        return self.embedding

    @property
    def size(self) -> int:
        """Get the size of the embedding vector."""
        return len(self.embedding)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "embedding": self.embedding,
            "model": self.model,
            "provider": self.provider,
            "dimensions": self.dimensions,
            "token_count": self.token_count,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingResult":
        """Create from dictionary."""
        return cls(
            text=data.get("text", ""),
            embedding=data.get("embedding", []),
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            dimensions=data.get("dimensions", 0),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
        )

    def similarity(self, other: "EmbeddingResult") -> float:
        """
        Calculate cosine similarity with another embedding.
        
        Args:
            other: Another EmbeddingResult to compare with.
        
        Returns:
            Cosine similarity score (0 to 1).
        """
        if len(self.embedding) != len(other.embedding):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(self.embedding, other.embedding))
        
        # Calculate magnitudes
        mag_a = sum(a * a for a in self.embedding) ** 0.5
        mag_b = sum(b * b for b in other.embedding) ** 0.5
        
        # Avoid division by zero
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        # Calculate cosine similarity
        return dot_product / (mag_a * mag_b)

    def __repr__(self) -> str:
        """Return string representation."""
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return (
            f"EmbeddingResult("
            f"text={text_preview!r}, "
            f"model={self.model}, "
            f"dimensions={self.dimensions})"
        )


@dataclass
class BatchEmbeddingResult:
    """
    Result from a batch embedding operation.
    
    Attributes:
        texts: List of original texts.
        embeddings: List of embedding vectors.
        model: Model used for embedding.
        provider: Provider used for embedding.
        dimensions: Number of dimensions in the embeddings.
        token_counts: List of token counts for each text.
        timestamp: When the embeddings were created.
        metadata: Additional metadata.
    """

    texts: List[str]
    embeddings: List[List[float]]
    model: str = ""
    provider: str = ""
    dimensions: int = 0
    token_counts: List[int] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """Get the number of embeddings."""
        return len(self.embeddings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "texts": self.texts,
            "embeddings": self.embeddings,
            "model": self.model,
            "provider": self.provider,
            "dimensions": self.dimensions,
            "token_counts": self.token_counts,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchEmbeddingResult":
        """Create from dictionary."""
        return cls(
            texts=data.get("texts", []),
            embeddings=data.get("embeddings", []),
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            dimensions=data.get("dimensions", 0),
            token_counts=data.get("token_counts", []),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BatchEmbeddingResult("
            f"count={self.count}, "
            f"model={self.model}, "
            f"dimensions={self.dimensions})"
        )
