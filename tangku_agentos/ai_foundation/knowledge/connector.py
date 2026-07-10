"""
AI Foundation Framework - Knowledge Connector

This module provides the KnowledgeConnector class for integrating with the Knowledge Engine.
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
class KnowledgeResult:
    """
    Result from a knowledge retrieval operation.
    
    Attributes:
        query: The original query.
        results: List of retrieved knowledge entries.
        scores: List of relevance scores for each result.
        count: Total number of results.
        metadata: Additional metadata.
    """

    query: str
    results: List[Any] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": self.results,
            "scores": self.scores,
            "count": self.count,
            "metadata": self.metadata,
        }


@dataclass
class KnowledgeConnectorMetrics:
    """Metrics for the knowledge connector."""
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


class KnowledgeConnector:
    """
    Connector for integrating with the Knowledge Engine.
    
    This class provides a unified interface for knowledge operations,
    abstracting the details of the underlying Knowledge Engine implementation.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import KnowledgeConnector
        >>> 
        >>> # Create connector
        >>> connector = KnowledgeConnector()
        >>> 
        >>> # Store knowledge
        >>> await connector.store("key", {"data": "value"})
        >>> 
        >>> # Retrieve knowledge
        >>> results = await connector.retrieve("query")
        >>> 
        >>> # Get specific knowledge
        >>> knowledge = await connector.get("key")
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the knowledge connector.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = KnowledgeConnectorMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        # Reference to the Knowledge Engine (will be set during initialization)
        self._knowledge_engine = None
        
        logger.info("KnowledgeConnector initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> KnowledgeConnectorMetrics:
        """Get the knowledge connector metrics."""
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
        Initialize the knowledge connector.
        
        This method connects to the Knowledge Engine.
        """
        if self._initialized:
            logger.warning("KnowledgeConnector already initialized")
            return
        
        logger.info("Initializing KnowledgeConnector...")
        
        try:
            # In a real implementation, this would connect to the Knowledge Engine
            # For now, we'll just mark as initialized
            self._initialized = True
            
            logger.info("KnowledgeConnector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeConnector: {e}")
            raise

    async def start(self) -> None:
        """
        Start the knowledge connector.
        """
        if self._started:
            logger.warning("KnowledgeConnector already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting KnowledgeConnector...")
        
        self._started = True
        logger.info("KnowledgeConnector started successfully")

    async def stop(self) -> None:
        """
        Stop the knowledge connector.
        """
        if not self._started:
            logger.warning("KnowledgeConnector not started")
            return
        
        logger.info("Stopping KnowledgeConnector...")
        
        self._started = False
        logger.info("KnowledgeConnector stopped successfully")

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeResult:
        """
        Retrieve knowledge entries matching the query.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            min_score: Minimum relevance score for results.
            metadata: Additional metadata for the retrieval.
        
        Returns:
            KnowledgeResult with retrieved knowledge entries.
        """
        async with self._lock:
            self._metrics.retrievals += 1
            
            try:
                # In a real implementation, this would call the Knowledge Engine
                # For now, return mock results
                results = []
                scores = []
                
                # Mock: return some sample knowledge entries
                for i in range(min(limit, 3)):
                    results.append({
                        "knowledge_id": f"knowledge_{i}",
                        "content": f"Sample knowledge related to: {query}",
                        "score": 0.9 - (i * 0.1),
                        "source": "knowledge_base",
                        "timestamp": datetime.utcnow().isoformat(),
                        "tags": ["sample", "knowledge"],
                    })
                    scores.append(0.9 - (i * 0.1))
                
                # Update metrics
                self._metrics.tokens_retrieved += sum(len(str(r)) for r in results)
                
                return KnowledgeResult(
                    query=query,
                    results=results,
                    scores=scores,
                    count=len(results),
                    metadata=metadata or {},
                )
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Knowledge retrieval failed: {e}")
                raise

    async def store(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store knowledge data.
        
        Args:
            key: Key for the knowledge entry.
            data: Data to store.
            metadata: Additional metadata.
            tags: Tags for categorizing the knowledge.
        
        Returns:
            Knowledge ID.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Knowledge Engine
                # For now, return a mock knowledge ID
                knowledge_id = f"knowledge_{hash(key) % 10000}"
                
                # Update metrics
                self._metrics.tokens_stored += len(str(data))
                
                return knowledge_id
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Knowledge storage failed: {e}")
                raise

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a specific knowledge entry by key.
        
        Args:
            key: Key of the knowledge entry.
        
        Returns:
            Knowledge data or None if not found.
        """
        async with self._lock:
            self._metrics.retrievals += 1
            
            try:
                # In a real implementation, this would call the Knowledge Engine
                # For now, return mock data
                return {
                    "knowledge_id": f"knowledge_{hash(key) % 10000}",
                    "content": f"Data for key: {key}",
                    "source": "knowledge_base",
                    "timestamp": datetime.utcnow().isoformat(),
                    "tags": ["sample"],
                }
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Knowledge get failed: {e}")
                raise

    async def update(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update a knowledge entry.
        
        Args:
            key: Key of the knowledge entry to update.
            data: New data for the knowledge entry.
            metadata: Additional metadata.
            tags: New tags for the knowledge entry.
        
        Returns:
            True if update was successful, False otherwise.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Knowledge Engine
                return True
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Knowledge update failed: {e}")
                raise

    async def delete(self, key: str) -> bool:
        """
        Delete a knowledge entry.
        
        Args:
            key: Key of the knowledge entry to delete.
        
        Returns:
            True if deletion was successful, False otherwise.
        """
        async with self._lock:
            self._metrics.storage_operations += 1
            
            try:
                # In a real implementation, this would call the Knowledge Engine
                return True
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Knowledge deletion failed: {e}")
                raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeResult:
        """
        Search knowledge with advanced filtering.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            filters: Additional filters for the search.
            tags: Tags to filter by.
        
        Returns:
            KnowledgeResult with search results.
        """
        # For now, just call retrieve
        return await self.retrieve(query, limit)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge connector.
        
        Returns:
            Dictionary with knowledge connector information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "enabled": self._config.knowledge.enabled,
                "max_results": self._config.knowledge.max_knowledge_results,
                "similarity_threshold": self._config.knowledge.knowledge_similarity_threshold,
                "retrieval_strategy": self._config.knowledge.retrieval_strategy,
            }
        }

    async def reset(self) -> None:
        """
        Reset the knowledge connector.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting KnowledgeConnector...")
        
        self._metrics = KnowledgeConnectorMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("KnowledgeConnector reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"KnowledgeConnector("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"retrievals={self._metrics.retrievals})"
        )
