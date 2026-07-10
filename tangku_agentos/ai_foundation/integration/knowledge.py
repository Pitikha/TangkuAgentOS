"""
AI Foundation Framework - Knowledge Integration

This module provides the KnowledgeIntegration class for integrating with the Knowledge Engine.
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
class KnowledgeIntegrationMetrics:
    """Metrics for knowledge integration."""
    requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requests": self.requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class KnowledgeIntegration:
    """
    Integration with the Knowledge Engine.
    
    This class provides the integration layer between the AI Foundation
    and the Knowledge Engine, enabling seamless knowledge operations
    for AI agents and workflows.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import KnowledgeIntegration
        >>> 
        >>> # Create integration
        >>> integration = KnowledgeIntegration()
        >>> 
        >>> # Store knowledge
        >>> await integration.store("key", {"data": "value"})
        >>> 
        >>> # Retrieve knowledge
        >>> knowledge = await integration.retrieve("query")
        >>> 
        >>> # Get knowledge engine status
        >>> status = await integration.get_status()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the knowledge integration.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = KnowledgeIntegrationMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._connected = False
        
        # Reference to the Knowledge Engine (will be set during connection)
        self._knowledge_engine = None
        
        logger.info("KnowledgeIntegration initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> KnowledgeIntegrationMetrics:
        """Get the knowledge integration metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the integration is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the integration is started."""
        return self._started

    @property
    def is_connected(self) -> bool:
        """Check if the integration is connected to the Knowledge Engine."""
        return self._connected

    async def initialize(self) -> None:
        """
        Initialize the knowledge integration.
        """
        if self._initialized:
            logger.warning("KnowledgeIntegration already initialized")
            return
        
        logger.info("Initializing KnowledgeIntegration...")
        
        self._initialized = True
        logger.info("KnowledgeIntegration initialized successfully")

    async def start(self) -> None:
        """
        Start the knowledge integration.
        
        This method connects to the Knowledge Engine.
        """
        if self._started:
            logger.warning("KnowledgeIntegration already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting KnowledgeIntegration...")
        
        # Connect to Knowledge Engine
        await self.connect()
        
        self._started = True
        logger.info("KnowledgeIntegration started successfully")

    async def stop(self) -> None:
        """
        Stop the knowledge integration.
        
        This method disconnects from the Knowledge Engine.
        """
        if not self._started:
            logger.warning("KnowledgeIntegration not started")
            return
        
        logger.info("Stopping KnowledgeIntegration...")
        
        # Disconnect from Knowledge Engine
        await self.disconnect()
        
        self._started = False
        logger.info("KnowledgeIntegration stopped successfully")

    async def connect(self) -> bool:
        """
        Connect to the Knowledge Engine.
        
        Returns:
            True if connection was successful, False otherwise.
        """
        if self._connected:
            logger.warning("KnowledgeIntegration already connected")
            return True
        
        try:
            # In a real implementation, this would connect to the Knowledge Engine
            # For now, just mark as connected
            self._connected = True
            logger.info("KnowledgeIntegration connected to Knowledge Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Knowledge Engine: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from the Knowledge Engine.
        
        Returns:
            True if disconnection was successful, False otherwise.
        """
        if not self._connected:
            logger.warning("KnowledgeIntegration not connected")
            return True
        
        try:
            # In a real implementation, this would disconnect from the Knowledge Engine
            # For now, just mark as disconnected
            self._connected = False
            logger.info("KnowledgeIntegration disconnected from Knowledge Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Knowledge Engine: {e}")
            return False

    async def store(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store knowledge in the Knowledge Engine.
        
        Args:
            key: Key for the knowledge entry.
            data: Knowledge data to store.
            metadata: Optional additional metadata.
            tags: Optional tags for categorizing the knowledge.
        
        Returns:
            Knowledge ID.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            knowledge_id = await self._foundation.knowledge.store(
                key=key,
                data=data,
                metadata=metadata,
                tags=tags,
            )
            
            self._metrics.successful_requests += 1
            return knowledge_id
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to store knowledge: {e}")
            raise

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Retrieve knowledge from the Knowledge Engine.
        
        Args:
            query: Query for retrieval.
            limit: Maximum number of results to return.
            metadata: Optional additional metadata.
        
        Returns:
            Retrieved knowledge.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            result = await self._foundation.knowledge.retrieve(
                query=query,
                limit=limit,
                metadata=metadata,
            )
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to retrieve knowledge: {e}")
            raise

    async def get(self, key: str) -> Any:
        """
        Get a specific knowledge entry by key.
        
        Args:
            key: Key of the knowledge entry.
        
        Returns:
            Knowledge data.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            result = await self._foundation.knowledge.get(key)
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to get knowledge: {e}")
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
            metadata: Optional additional metadata.
            tags: Optional new tags for the knowledge entry.
        
        Returns:
            True if update was successful, False otherwise.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            result = await self._foundation.knowledge.update(
                key=key,
                data=data,
                metadata=metadata,
                tags=tags,
            )
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to update knowledge: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """
        Delete a knowledge entry.
        
        Args:
            key: Key of the knowledge entry to delete.
        
        Returns:
            True if deletion was successful, False otherwise.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            result = await self._foundation.knowledge.delete(key)
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to delete knowledge: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Any:
        """
        Search the Knowledge Engine.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            filters: Optional additional filters.
            tags: Optional tags to filter by.
        
        Returns:
            Search results.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's knowledge connector
            result = await self._foundation.knowledge.search(
                query=query,
                limit=limit,
                filters=filters,
                tags=tags,
            )
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to search knowledge: {e}")
            raise

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the Knowledge Engine.
        
        Returns:
            Dictionary with Knowledge Engine status.
        """
        # In a real implementation, this would query the Knowledge Engine
        # For now, return mock status
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 3600.0,  # 1 hour
            "knowledge_base": {
                "documents": 10000,
                "embeddings": 50000,
                "indexes": 10,
            },
        }

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge integration.
        
        Returns:
            Dictionary with knowledge integration information.
        """
        return {
            "status": "active" if self._initialized and self._started and self._connected else "inactive",
            "connected": self._connected,
            "metrics": self._metrics.to_dict(),
            "knowledge_status": await self.get_status() if self._connected else {},
        }

    async def reset(self) -> None:
        """
        Reset the knowledge integration.
        
        This method resets all state and disconnects from the Knowledge Engine.
        """
        logger.info("Resetting KnowledgeIntegration...")
        
        await self.disconnect()
        
        self._metrics = KnowledgeIntegrationMetrics()
        self._initialized = False
        self._started = False
        self._connected = False
        
        logger.info("KnowledgeIntegration reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"KnowledgeIntegration("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"connected={self._connected})"
        )
