"""
Embeddings package for the AI Foundation Framework.

This package provides embedding capabilities for TangkuAgentOS,
including embedding generation, caching, batching, and similarity calculation.
"""

from .embedding_registry import EmbeddingRegistry
from .embedding_cache import EmbeddingCache
from .embedding_batch import EmbeddingBatcher
from .embedding_similarity import EmbeddingSimilarity

__all__ = [
    "EmbeddingRegistry",
    "EmbeddingCache",
    "EmbeddingBatcher",
    "EmbeddingSimilarity",
]
