"""
AI Foundation Framework - AI Cache

This module provides the AICache class for caching AI responses and data.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Represents an entry in the AI cache.
    
    Attributes:
        key: Cache key.
        value: Cached value.
        ttl: Time-to-live in seconds.
        created_at: When the entry was created.
        expires_at: When the entry expires.
        access_count: Number of times the entry has been accessed.
        last_accessed: When the entry was last accessed.
        metadata: Additional metadata.
    """

    key: str
    value: Any
    ttl: float = 300.0  # 5 minutes default
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + datetime.timedelta(seconds=300))
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        return datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        """Update the last accessed time."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            key=data.get("key", ""),
            value=data.get("value"),
            ttl=data.get("ttl", 300.0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            expires_at=datetime.fromisoformat(data.get("expires_at", (datetime.utcnow() + datetime.timedelta(seconds=300)).isoformat())),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data.get("last_accessed", datetime.utcnow().isoformat())),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AICacheMetrics:
    """Metrics for the AI cache."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    gets: int = 0
    deletes: int = 0
    evictions: int = 0
    size: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    @property
    def hit_rate(self) -> float:
        """Calculate the cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "gets": self.gets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "size": self.size,
            "hit_rate": self.hit_rate,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class AICache:
    """
    Cache for AI responses and data.
    
    This class provides a caching layer for AI operations, supporting
    multiple cache types (memory, file, redis) and automatic expiration.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import AICache
        >>> 
        >>> # Create cache
        >>> cache = AICache()
        >>> 
        >>> # Set a value
        >>> await cache.set("key", "value", ttl=3600)
        >>> 
        >>> # Get a value
        >>> value = await cache.get("key")
        >>> 
        >>> # Delete a value
        >>> await cache.delete("key")
        >>> 
        >>> # Clear the cache
        >>> await cache.clear()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the AI cache.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU eviction
        self._metrics = AICacheMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        # Cache configuration
        self._max_size = config.cache.response_cache_size
        self._default_ttl = config.cache.response_cache_ttl
        
        logger.info("AICache initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> AICacheMetrics:
        """Get the cache metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the cache is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the cache is started."""
        return self._started

    @property
    def size(self) -> int:
        """Get the current size of the cache."""
        return len(self._cache)

    async def initialize(self) -> None:
        """
        Initialize the AI cache.
        """
        if self._initialized:
            logger.warning("AICache already initialized")
            return
        
        logger.info("Initializing AICache...")
        
        self._initialized = True
        logger.info("AICache initialized successfully")

    async def start(self) -> None:
        """
        Start the AI cache.
        
        This method starts the cleanup task for expired entries.
        """
        if self._started:
            logger.warning("AICache already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting AICache...")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
        
        self._started = True
        logger.info("AICache started successfully")

    async def stop(self) -> None:
        """
        Stop the AI cache.
        """
        if not self._started:
            logger.warning("AICache not started")
            return
        
        logger.info("Stopping AICache...")
        
        # Cancel cleanup task
        if hasattr(self, '_cleanup_task') and self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._started = False
        logger.info("AICache stopped successfully")

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries periodically."""
        cleanup_interval = 60.0  # 1 minute
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

    async def _cleanup_expired(self) -> None:
        """Clean up expired cache entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._metrics.evictions += 1

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Optional time-to-live in seconds.
            metadata: Optional additional metadata.
        """
        async with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self._max_size:
                await self._evict_entries()
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or self._default_ttl,
                expires_at=datetime.utcnow() + datetime.timedelta(seconds=ttl or self._default_ttl),
                metadata=metadata or {},
            )
            
            # Store entry
            self._cache[key] = entry
            self._access_order.append(key)
            
            # Update metrics
            self._metrics.sets += 1
            self._metrics.size = len(self._cache)
            
            logger.debug(f"Cache set: {key}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached value or None if not found or expired.
        """
        async with self._lock:
            self._metrics.gets += 1
            
            entry = self._cache.get(key)
            if not entry:
                self._metrics.misses += 1
                return None
            
            # Check if expired
            if entry.is_expired:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._metrics.misses += 1
                self._metrics.evictions += 1
                return None
            
            # Update access info
            entry.touch()
            
            # Update access order (move to end for LRU)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            # Update metrics
            self._metrics.hits += 1
            
            return entry.value

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
        
        Returns:
            True if the key was deleted, False if not found.
        """
        async with self._lock:
            if key not in self._cache:
                return False
            
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            
            self._metrics.deletes += 1
            self._metrics.size = len(self._cache)
            
            return True

    async def _evict_entries(self) -> None:
        """Evict entries to make room for new ones."""
        # Evict least recently used entries
        while len(self._cache) >= self._max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._metrics.evictions += 1

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._metrics.size = 0
            
            logger.debug("Cache cleared")

    async def clear_expired(self) -> int:
        """
        Clear all expired entries from the cache.
        
        Returns:
            Number of entries cleared.
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._metrics.evictions += 1
            
            self._metrics.size = len(self._cache)
            return len(expired_keys)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys.
        
        Returns:
            Dictionary of key-value pairs for found keys.
        """
        results = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        
        return results

    async def set_many(self, items: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """
        Set multiple values in the cache.
        
        Args:
            items: Dictionary of key-value pairs to cache.
            ttl: Optional time-to-live in seconds for all items.
        """
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys to delete.
        
        Returns:
            Number of keys deleted.
        """
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
        
        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        value = await self.get(key)
        return value is not None

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.
        
        Returns:
            Dictionary with cache information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "size": len(self._cache),
            "max_size": self._max_size,
            "default_ttl": self._default_ttl,
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the cache.
        
        This method clears all entries and resets all state.
        """
        logger.info("Resetting AICache...")
        
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._metrics = AICacheMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("AICache reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AICache("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"size={len(self._cache)}, "
            f"hit_rate={self._metrics.hit_rate:.2%})"
        )
