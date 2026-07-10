"""
AI Foundation Framework - Embedding Manager

This module provides the EmbeddingManager class for managing embeddings.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.embeddings.embedding import EmbeddingResult, BatchEmbeddingResult
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingManagerMetrics:
    """Metrics for the embedding manager."""
    embeddings_generated: int = 0
    batch_embeddings_generated: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_processed: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "embeddings_generated": self.embeddings_generated,
            "batch_embeddings_generated": self.batch_embeddings_generated,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "tokens_processed": self.tokens_processed,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class EmbeddingManager:
    """
    Manager for AI embeddings.
    
    This class provides a unified interface for generating and managing
    embeddings. It supports multiple embedding providers, caching,
    and batch processing.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import EmbeddingManager
        >>> 
        >>> # Create manager
        >>> manager = EmbeddingManager()
        >>> 
        >>> # Generate an embedding
        >>> result = await manager.embed("Hello, world!")
        >>> 
        >>> # Generate batch embeddings
        >>> results = await manager.embed_batch(["Hello", "World"])
        >>> 
        >>> # Calculate similarity
        >>> similarity = result.similarity(other_result)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the embedding manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._cache: Dict[str, "EmbeddingResult"] = {}
        self._batch_cache: Dict[str, "BatchEmbeddingResult"] = {}
        self._metrics = EmbeddingManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("EmbeddingManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> EmbeddingManagerMetrics:
        """Get the embedding manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the embedding manager.
        """
        if self._initialized:
            logger.warning("EmbeddingManager already initialized")
            return
        
        logger.info("Initializing EmbeddingManager...")
        
        self._initialized = True
        logger.info("EmbeddingManager initialized successfully")

    async def start(self) -> None:
        """
        Start the embedding manager.
        """
        if self._started:
            logger.warning("EmbeddingManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting EmbeddingManager...")
        
        self._started = True
        logger.info("EmbeddingManager started successfully")

    async def stop(self) -> None:
        """
        Stop the embedding manager.
        """
        if not self._started:
            logger.warning("EmbeddingManager not started")
            return
        
        logger.info("Stopping EmbeddingManager...")
        
        self._started = False
        logger.info("EmbeddingManager stopped successfully")

    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        use_cache: bool = True,
    ) -> "EmbeddingResult":
        """
        Generate an embedding for the given text.
        
        Args:
            text: Text to embed.
            model: Model to use for embedding.
            provider: Provider to use for embedding.
            use_cache: Whether to use caching.
        
        Returns:
            EmbeddingResult with the generated embedding.
        """
        async with self._lock:
            # Check cache
            if use_cache:
                cache_key = self._generate_cache_key(text, model, provider)
                if cache_key in self._cache:
                    self._metrics.cache_hits += 1
                    return self._cache[cache_key]
                self._metrics.cache_misses += 1
            
            # Generate embedding
            result = await self._generate_embedding(text, model, provider)
            
            # Update metrics
            self._metrics.embeddings_generated += 1
            self._metrics.tokens_processed += result.token_count
            
            # Cache the result
            if use_cache:
                self._cache[cache_key] = result
            
            return result

    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        use_cache: bool = True,
    ) -> "BatchEmbeddingResult":
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed.
            model: Model to use for embedding.
            provider: Provider to use for embedding.
            use_cache: Whether to use caching.
        
        Returns:
            BatchEmbeddingResult with the generated embeddings.
        """
        async with self._lock:
            # Check cache
            if use_cache:
                cache_key = self._generate_batch_cache_key(texts, model, provider)
                if cache_key in self._batch_cache:
                    self._metrics.cache_hits += 1
                    return self._batch_cache[cache_key]
                self._metrics.cache_misses += 1
            
            # Generate embeddings
            result = await self._generate_batch_embedding(texts, model, provider)
            
            # Update metrics
            self._metrics.batch_embeddings_generated += 1
            self._metrics.tokens_processed += sum(result.token_counts)
            
            # Cache the result
            if use_cache:
                self._batch_cache[cache_key] = result
            
            return result

    def _generate_cache_key(self, text: str, model: Optional[str], provider: Optional[str]) -> str:
        """Generate a cache key for an embedding."""
        model_str = model or self._config.embeddings.default_embedding_model
        provider_str = provider or self._config.providers.default_provider
        return hashlib.sha256(f"{model_str}:{provider_str}:{text}".encode()).hexdigest()

    def _generate_batch_cache_key(
        self,
        texts: List[str],
        model: Optional[str],
        provider: Optional[str],
    ) -> str:
        """Generate a cache key for batch embeddings."""
        model_str = model or self._config.embeddings.default_embedding_model
        provider_str = provider or self._config.providers.default_provider
        texts_str = ",".join(texts)
        return hashlib.sha256(f"batch:{model_str}:{provider_str}:{texts_str}".encode()).hexdigest()

    async def _generate_embedding(
        self,
        text: str,
        model: Optional[str],
        provider: Optional[str],
    ) -> "EmbeddingResult":
        """
        Generate an embedding using the specified model and provider.
        
        Args:
            text: Text to embed.
            model: Model to use.
            provider: Provider to use.
        
        Returns:
            EmbeddingResult with the generated embedding.
        """
        from tangku_agentos.ai_foundation.embeddings.embedding import EmbeddingResult
        
        # Use default model and provider if not specified
        model = model or self._config.embeddings.default_embedding_model
        provider = provider or self._config.providers.default_provider
        
        # In a real implementation, this would call the appropriate provider
        # For now, generate a mock embedding
        
        # Calculate token count (rough estimate)
        token_count = len(text) // 4
        
        # Generate mock embedding vector (1536 dimensions for text-embedding-3-small)
        dimensions = 1536
        embedding = [0.1 * (i % 10) for i in range(dimensions)]
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=model,
            provider=provider,
            dimensions=dimensions,
            token_count=token_count,
            metadata={"mock": True},
        )

    async def _generate_batch_embedding(
        self,
        texts: List[str],
        model: Optional[str],
        provider: Optional[str],
    ) -> "BatchEmbeddingResult":
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed.
            model: Model to use.
            provider: Provider to use.
        
        Returns:
            BatchEmbeddingResult with the generated embeddings.
        """
        from tangku_agentos.ai_foundation.embeddings.embedding import BatchEmbeddingResult
        
        # Use default model and provider if not specified
        model = model or self._config.embeddings.default_embedding_model
        provider = provider or self._config.providers.default_provider
        
        # Generate embeddings for each text
        embeddings = []
        token_counts = []
        
        for text in texts:
            result = await self._generate_embedding(text, model, provider)
            embeddings.append(result.embedding)
            token_counts.append(result.token_count)
        
        return BatchEmbeddingResult(
            texts=texts,
            embeddings=embeddings,
            model=model,
            provider=provider,
            dimensions=len(embeddings[0]) if embeddings else 0,
            token_counts=token_counts,
            metadata={"mock": True},
        )

    async def calculate_similarity(
        self,
        text1: str,
        text2: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            model: Model to use for embedding.
            provider: Provider to use for embedding.
        
        Returns:
            Similarity score (0 to 1).
        """
        # Generate embeddings for both texts
        result1 = await self.embed(text1, model, provider)
        result2 = await self.embed(text2, model, provider)
        
        # Calculate similarity
        return result1.similarity(result2)

    async def search(
        self,
        query: str,
        texts: List[str],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts.
        
        Args:
            query: Query text.
            texts: List of texts to search through.
            model: Model to use for embedding.
            provider: Provider to use for embedding.
            limit: Maximum number of results to return.
        
        Returns:
            List of search results with similarity scores.
        """
        # Generate embedding for query
        query_result = await self.embed(query, model, provider)
        
        # Generate embeddings for all texts
        batch_result = await self.embed_batch(texts, model, provider)
        
        # Calculate similarities
        results = []
        for i, embedding in enumerate(batch_result.embeddings):
            similarity = query_result.similarity(EmbeddingResult(
                text=texts[i],
                embedding=embedding,
            ))
            results.append({
                "text": texts[i],
                "similarity": similarity,
                "index": i,
            })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return top results
        return results[:limit]

    async def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        self._batch_cache.clear()

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding manager.
        
        Returns:
            Dictionary with embedding manager information.
        """
        return {
            "cache_size": len(self._cache),
            "batch_cache_size": len(self._batch_cache),
            "metrics": self._metrics.to_dict(),
            "config": {
                "default_model": self._config.embeddings.default_embedding_model,
                "cache_enabled": self._config.embeddings.cache_enabled,
                "cache_size": self._config.embeddings.cache_size,
                "batch_size": self._config.embeddings.batch_size,
            }
        }

    async def reset(self) -> None:
        """
        Reset the embedding manager.
        
        This method clears all state and metrics.
        """
        logger.info("Resetting EmbeddingManager...")
        
        self._cache.clear()
        self._batch_cache.clear()
        self._metrics = EmbeddingManagerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("EmbeddingManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"EmbeddingManager("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"cache={len(self._cache)})"
        )
