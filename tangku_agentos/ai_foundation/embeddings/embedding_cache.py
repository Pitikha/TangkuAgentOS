"""
Embedding Cache for TangkuAgentOS AI Foundation Framework.

Caches embedding results to improve performance and reduce costs.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached embedding entry."""
    key: str
    embedding: List[float]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingCache:
    """Caches embedding results for TangkuAgentOS.

    This class provides caching for embedding operations to reduce
    latency and costs for repeated embedding requests.
    """

    def __init__(self, default_ttl: int = 3600):
        """Initialize the EmbeddingCache.

        Args:
            default_ttl: Default time-to-live for cache entries in seconds.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        logger.info(f"EmbeddingCache initialized with default TTL of {default_ttl} seconds.")

    async def get(self, key: str) -> Optional[List[float]]:
        """Retrieve an embedding from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached embedding if found and not expired, otherwise None.
        """
        entry = self._cache.get(key)
        if entry and entry.expires_at > datetime.utcnow():
            logger.debug(f"Cache hit for embedding key: {key}")
            return entry.embedding
        logger.debug(f"Cache miss for embedding key: {key}")
        return None

    async def set(
        self,
        key: str,
        embedding: List[float],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store an embedding in the cache.

        Args:
            key: The cache key.
            embedding: The embedding vector to cache.
            ttl: Time-to-live for the cache entry in seconds.
            metadata: Optional metadata for the cache entry.
        """
        expires_at = datetime.utcnow() + timedelta(seconds=ttl or self._default_ttl)
        self._cache[key] = CacheEntry(
            key=key,
            embedding=embedding,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata or {},
        )
        logger.debug(f"Cached embedding for key: {key}")

    async def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry.

        Args:
            key: The cache key to invalidate.

        Returns:
            True if the entry was invalidated, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache entry for embedding key: {key}")
            return True
        return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cleared all embedding cache entries.")

    async def cleanup(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at <= datetime.utcnow()
        ]
        for key in expired_keys:
            del self._cache[key]
        logger.debug(f"Cleaned up {len(expired_keys)} expired embedding cache entries.")
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics.
        """
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values()
            if entry.expires_at <= datetime.utcnow()
        )
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
        }
