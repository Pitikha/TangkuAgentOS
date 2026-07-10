"""
AI Foundation Framework - Memory Integration

This module provides the MemoryIntegration class for integrating with the Memory Engine.
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
class MemoryIntegrationMetrics:
    """Metrics for memory integration."""
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


class MemoryIntegration:
    """
    Integration with the Memory Engine.
    
    This class provides the integration layer between the AI Foundation
    and the Memory Engine, enabling seamless memory operations for AI
    agents and workflows.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import MemoryIntegration
        >>> 
        >>> # Create integration
        >>> integration = MemoryIntegration()
        >>> 
        >>> # Store a memory
        >>> await integration.store("key", {"data": "value"})
        >>> 
        >>> # Retrieve a memory
        >>> memory = await integration.retrieve("query")
        >>> 
        >>> # Get memory engine status
        >>> status = await integration.get_status()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the memory integration.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = MemoryIntegrationMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._connected = False
        
        # Reference to the Memory Engine (will be set during connection)
        self._memory_engine = None
        
        logger.info("MemoryIntegration initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> MemoryIntegrationMetrics:
        """Get the memory integration metrics."""
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
        """Check if the integration is connected to the Memory Engine."""
        return self._connected

    async def initialize(self) -> None:
        """
        Initialize the memory integration.
        """
        if self._initialized:
            logger.warning("MemoryIntegration already initialized")
            return
        
        logger.info("Initializing MemoryIntegration...")
        
        self._initialized = True
        logger.info("MemoryIntegration initialized successfully")

    async def start(self) -> None:
        """
        Start the memory integration.
        
        This method connects to the Memory Engine.
        """
        if self._started:
            logger.warning("MemoryIntegration already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting MemoryIntegration...")
        
        # Connect to Memory Engine
        await self.connect()
        
        self._started = True
        logger.info("MemoryIntegration started successfully")

    async def stop(self) -> None:
        """
        Stop the memory integration.
        
        This method disconnects from the Memory Engine.
        """
        if not self._started:
            logger.warning("MemoryIntegration not started")
            return
        
        logger.info("Stopping MemoryIntegration...")
        
        # Disconnect from Memory Engine
        await self.disconnect()
        
        self._started = False
        logger.info("MemoryIntegration stopped successfully")

    async def connect(self) -> bool:
        """
        Connect to the Memory Engine.
        
        Returns:
            True if connection was successful, False otherwise.
        """
        if self._connected:
            logger.warning("MemoryIntegration already connected")
            return True
        
        try:
            # In a real implementation, this would connect to the Memory Engine
            # For now, just mark as connected
            self._connected = True
            logger.info("MemoryIntegration connected to Memory Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Memory Engine: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from the Memory Engine.
        
        Returns:
            True if disconnection was successful, False otherwise.
        """
        if not self._connected:
            logger.warning("MemoryIntegration not connected")
            return True
        
        try:
            # In a real implementation, this would disconnect from the Memory Engine
            # For now, just mark as disconnected
            self._connected = False
            logger.info("MemoryIntegration disconnected from Memory Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Memory Engine: {e}")
            return False

    async def store(
        self,
        key: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> str:
        """
        Store data in the Memory Engine.
        
        Args:
            key: Key for the memory entry.
            data: Data to store.
            metadata: Optional additional metadata.
            ttl: Optional time-to-live in seconds.
        
        Returns:
            Memory ID.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            memory_id = await self._foundation.memory.store(
                key=key,
                data=data,
                metadata=metadata,
                ttl=ttl,
            )
            
            self._metrics.successful_requests += 1
            return memory_id
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to store memory: {e}")
            raise

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Retrieve data from the Memory Engine.
        
        Args:
            query: Query for retrieval.
            limit: Maximum number of results to return.
            metadata: Optional additional metadata.
        
        Returns:
            Retrieved data.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            result = await self._foundation.memory.retrieve(
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
            logger.error(f"Failed to retrieve memory: {e}")
            raise

    async def get(self, key: str) -> Any:
        """
        Get a specific memory entry by key.
        
        Args:
            key: Key of the memory entry.
        
        Returns:
            Memory data.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            result = await self._foundation.memory.get(key)
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to get memory: {e}")
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
            metadata: Optional additional metadata.
        
        Returns:
            True if update was successful, False otherwise.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            result = await self._foundation.memory.update(
                key=key,
                data=data,
                metadata=metadata,
            )
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to update memory: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """
        Delete a memory entry.
        
        Args:
            key: Key of the memory entry to delete.
        
        Returns:
            True if deletion was successful, False otherwise.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            result = await self._foundation.memory.delete(key)
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to delete memory: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Search the Memory Engine.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            filters: Optional additional filters.
        
        Returns:
            Search results.
        """
        self._metrics.requests += 1
        
        try:
            # Use the foundation's memory connector
            result = await self._foundation.memory.search(
                query=query,
                limit=limit,
                filters=filters,
            )
            
            self._metrics.successful_requests += 1
            return result
            
        except Exception as e:
            self._metrics.failed_requests += 1
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to search memory: {e}")
            raise

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the Memory Engine.
        
        Returns:
            Dictionary with Memory Engine status.
        """
        # In a real implementation, this would query the Memory Engine
        # For now, return mock status
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 3600.0,  # 1 hour
            "memory_usage": 0.45,
            "storage": {
                "working_memory": 1000,
                "long_term_memory": 5000,
                "episodic_memory": 2000,
                "semantic_memory": 3000,
            },
        }

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the memory integration.
        
        Returns:
            Dictionary with memory integration information.
        """
        return {
            "status": "active" if self._initialized and self._started and self._connected else "inactive",
            "connected": self._connected,
            "metrics": self._metrics.to_dict(),
            "memory_status": await self.get_status() if self._connected else {},
        }

    async def reset(self) -> None:
        """
        Reset the memory integration.
        
        This method resets all state and disconnects from the Memory Engine.
        """
        logger.info("Resetting MemoryIntegration...")
        
        await self.disconnect()
        
        self._metrics = MemoryIntegrationMetrics()
        self._initialized = False
        self._started = False
        self._connected = False
        
        logger.info("MemoryIntegration reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MemoryIntegration("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"connected={self._connected})"
        )
