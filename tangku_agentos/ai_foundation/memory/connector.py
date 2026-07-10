"""
AI Foundation Framework - Memory Connector

This module provides the MemoryConnector class for integrating with the Memory Engine.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class MemoryResult:
    """
    Result from a memory retrieval operation.
    
    Attributes:
        query: The original query.
        results: List of retrieved memory entries.
        scores: List of relevance scores for each result.
        metadata: Additional metadata.
    """

    query: str
    results: List[Any] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": self.results,
            "scores": self.scores,
            "metadata": self.metadata,
        }


@dataclass
class MemoryConnectorMetrics:
    """Metrics for the memory connector."""
    retrievals: int = 0
    storage_operations: int = 0
    tokens_retrieved: int = 0
    tokens_stored: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "retrievals": self.retrievals,
            "storage_operations": self.storage_operations,
            "tokens_retrieved": self.tokens_retrieved,
            "tokens_stored": self.tokens_stored,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class MemoryConnector:
    """
    Connector for integrating with the Memory Engine.
    
    This class provides a unified interface for memory operations,
    abstracting the details of the underlying Memory Engine implementation.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import MemoryConnector
        >>> 
        >>> # Create connector
        >>> connector = MemoryConnector()
        >>> 
        >>> # Store a memory
        >>> await connector.store("key", {"data": "value"})
        >>> 
        >>> # Retrieve memories
        >>> results = await connector.retrieve("query")
        >>> 
        >>> # Get a specific memory
        >>> memory = await connector.get("key")
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the memory connector.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = MemoryConnectorMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        # Reference to the Memory Engine (will be set during initialization)
        self._memory_engine = None
        
        logger.info("MemoryConnector initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> MemoryConnectorMetrics:
        """Get the memory connector metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the connector is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the connector is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the memory connector.
        
        This method connects to the Memory Engine.
        """
        if self._initialized:
            logger.warning("MemoryConnector already initialized")
            return
        
        logger.info("Initializing MemoryConnector...")
        
        try:
            # In a real implementation, this would connect to the Memory Engine
            # For now, we'll just mark as initialized
            self._initialized = True
            
            logger.info("MemoryConnector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MemoryConnector: {e}")
            raise

    async def start(self) -> None:
        """
        Start the memory connector.
        """
        if self._started:
            logger.warning("MemoryConnector already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting MemoryConnector...")
        
        self._started = True
        logger.info("MemoryConnector started successfully")

    async def stop(self) -> None:
        """
        Stop the memory connector.
        """
        if not self._started:
            logger.warning("MemoryConnector not started")
            return
        
        logger.info("Stopping MemoryConnector...")
        
        self._started = False
        logger.info("MemoryConnector stopped successfully")

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryResult:
        """
        Retrieve memories matching the query.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            min_score: Minimum relevance score for results.
            metadata: Additional metadata for the retrieval.
        
        Returns:
            MemoryResult with retrieved memories.
        """
        async with self._lock:
            self._metrics.retrievals += 1
            
            try:
                # In a real implementation, this would call the Memory Engine
                # For now, return mock results
                results = []
                scores = []
                
                # Mock: return some sample memories
                for i in range(min(limit, 3)):
                    results.append({
                        "memory_id": f"memory_{i}",
                        "content": f"Sample memory related to: {query}",
                        "score": 0.9 - (i * 0.1),
                        "source": "working_memory",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    scores.append(0.9 - (i * 0.1))
                
                # Update metrics
                self._metrics.tokens_retrieved += sum(len(str(r)) for r in results)
                
                return MemoryResult(
                    query=query,
                    results=results,
                    scores=scores,
                    metadata=metadata or {},
                )
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Memory retrieval failed: {e}")
                raise

    async def store(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> str:
        """
        Store data in memory.
        
        Args:
            key: Key for the memory entry.
            data: Data to store.
            metadata: Additional metadata.
            ttl: Time-to-live in seconds.
        
        Returns:
            Memory ID.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Memory Engine
                # For now, return a mock memory ID
                memory_id = f"memory_{hash(key) % 10000}"
                
                # Update metrics
                self._metrics.tokens_stored += len(str(data))
                
                return memory_id
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Memory storage failed: {e}")
                raise

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a specific memory entry by key.
        
        Args:
            key: Key of the memory entry.
        
        Returns:
            Memory data or None if not found.
        """
        async with self._lock:
            self._metrics.retrievals += 1
            
            try:
                # In a real implementation, this would call the Memory Engine
                # For now, return mock data
                return {
                    "memory_id": f"memory_{hash(key) % 10000}",
                    "content": f"Data for key: {key}",
                    "source": "working_memory",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Memory get failed: {e}")
                raise

    async def update(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a memory entry.
        
        Args:
            key: Key of the memory entry to update.
            data: New data for the memory entry.
            metadata: Additional metadata.
        
        Returns:
            True if update was successful, False otherwise.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Memory Engine
                return True
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Memory update failed: {e}")
                raise

    async def delete(self, key: str) -> bool:
        """
        Delete a memory entry.
        
        Args:
            key: Key of the memory entry to delete.
        
        Returns:
            True if deletion was successful, False otherwise.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Memory Engine
                return True
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Memory deletion failed: {e}")
                raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> MemoryResult:
        """
        Search memories with advanced filtering.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            filters: Additional filters for the search.
        
        Returns:
            MemoryResult with search results.
        """
        # For now, just call retrieve
        return await self.retrieve(query, limit)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the memory connector.
        
        Returns:
            Dictionary with memory connector information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "enabled": self._config.memory.enabled,
                "max_results": self._config.memory.max_memory_results,
                "similarity_threshold": self._config.memory.memory_similarity_threshold,
            }
        }

    async def reset(self) -> None:
        """
        Reset the memory connector.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting MemoryConnector...")
        
        self._metrics = MemoryConnectorMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("MemoryConnector reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MemoryConnector("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"retrievals={self._metrics.retrievals})"
        )
