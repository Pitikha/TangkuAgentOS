"""
AI Foundation Framework - Kernel Integration

This module provides the KernelIntegration class for integrating with the Kernel Runtime.
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
class KernelIntegrationMetrics:
    """Metrics for kernel integration."""
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


class KernelIntegration:
    """
    Integration with the Kernel Runtime.
    
    This class provides the integration layer between the AI Foundation
    and the Kernel Runtime, enabling communication and coordination
    between AI operations and the kernel's runtime management.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import KernelIntegration
        >>> 
        >>> # Create integration
        >>> integration = KernelIntegration()
        >>> 
        >>> # Register with kernel
        >>> await integration.register()
        >>> 
        >>> # Notify kernel of AI operation
        >>> await integration.notify_operation_start("ai_request", request)
        >>> 
        >>> # Get kernel status
        >>> status = await integration.get_kernel_status()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the kernel integration.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = KernelIntegrationMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._registered = False
        
        # Reference to the Kernel (will be set during registration)
        self._kernel = None
        
        logger.info("KernelIntegration initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> KernelIntegrationMetrics:
        """Get the kernel integration metrics."""
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
    def is_registered(self) -> bool:
        """Check if the integration is registered with the kernel."""
        return self._registered

    async def initialize(self) -> None:
        """
        Initialize the kernel integration.
        """
        if self._initialized:
            logger.warning("KernelIntegration already initialized")
            return
        
        logger.info("Initializing KernelIntegration...")
        
        self._initialized = True
        logger.info("KernelIntegration initialized successfully")

    async def start(self) -> None:
        """
        Start the kernel integration.
        
        This method registers with the Kernel Runtime.
        """
        if self._started:
            logger.warning("KernelIntegration already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting KernelIntegration...")
        
        # Register with the kernel
        await self.register()
        
        self._started = True
        logger.info("KernelIntegration started successfully")

    async def stop(self) -> None:
        """
        Stop the kernel integration.
        
        This method unregisters from the Kernel Runtime.
        """
        if not self._started:
            logger.warning("KernelIntegration not started")
            return
        
        logger.info("Stopping KernelIntegration...")
        
        # Unregister from the kernel
        await self.unregister()
        
        self._started = False
        logger.info("KernelIntegration stopped successfully")

    async def register(self) -> bool:
        """
        Register with the Kernel Runtime.
        
        Returns:
            True if registration was successful, False otherwise.
        """
        if self._registered:
            logger.warning("KernelIntegration already registered")
            return True
        
        try:
            # In a real implementation, this would connect to the Kernel Runtime
            # For now, just mark as registered
            self._registered = True
            logger.info("KernelIntegration registered with Kernel Runtime")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register with Kernel Runtime: {e}")
            return False

    async def unregister(self) -> bool:
        """
        Unregister from the Kernel Runtime.
        
        Returns:
            True if unregistration was successful, False otherwise.
        """
        if not self._registered:
            logger.warning("KernelIntegration not registered")
            return True
        
        try:
            # In a real implementation, this would disconnect from the Kernel Runtime
            # For now, just mark as unregistered
            self._registered = False
            logger.info("KernelIntegration unregistered from Kernel Runtime")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister from Kernel Runtime: {e}")
            return False

    async def notify_operation_start(
        self,
        operation_type: str,
        operation_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Notify the kernel that an AI operation is starting.
        
        Args:
            operation_type: Type of the operation.
            operation_id: Unique identifier for the operation.
            context: Optional additional context.
        
        Returns:
            True if notification was successful, False otherwise.
        """
        self._metrics.requests += 1
        
        try:
            # In a real implementation, this would notify the Kernel Runtime
            # For now, just log
            logger.debug(f"AI operation started: {operation_type} ({operation_id})")
            return True
            
        except Exception as e:
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to notify operation start: {e}")
            return False

    async def notify_operation_end(
        self,
        operation_type: str,
        operation_id: str,
        success: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Notify the kernel that an AI operation has ended.
        
        Args:
            operation_type: Type of the operation.
            operation_id: Unique identifier for the operation.
            success: Whether the operation was successful.
            context: Optional additional context.
        
        Returns:
            True if notification was successful, False otherwise.
        """
        if success:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1
        
        try:
            # In a real implementation, this would notify the Kernel Runtime
            # For now, just log
            logger.debug(f"AI operation ended: {operation_type} ({operation_id}) - {'success' if success else 'failed'}")
            return True
            
        except Exception as e:
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"Failed to notify operation end: {e}")
            return False

    async def get_kernel_status(self) -> Dict[str, Any]:
        """
        Get the status of the Kernel Runtime.
        
        Returns:
            Dictionary with kernel status information.
        """
        # In a real implementation, this would query the Kernel Runtime
        # For now, return mock status
        return {
            "status": "running",
            "version": "1.0.0",
            "uptime": 3600.0,  # 1 hour
            "components": {
                "runtime_communication": "healthy",
                "memory_engine": "healthy",
                "knowledge_engine": "healthy",
                "provider_runtime": "healthy",
            },
        }

    async def get_ai_status(self) -> Dict[str, Any]:
        """
        Get the status of AI operations from the kernel's perspective.
        
        Returns:
            Dictionary with AI status information.
        """
        # In a real implementation, this would query the Kernel Runtime
        # For now, return mock status
        return {
            "ai_operations": {
                "active": 5,
                "pending": 2,
                "completed": 100,
                "failed": 1,
            },
            "resource_usage": {
                "cpu": 0.45,
                "memory": 0.67,
                "gpu": 0.33,
            },
        }

    async def request_resource(self, resource_type: str, amount: int) -> bool:
        """
        Request resources from the kernel.
        
        Args:
            resource_type: Type of resource to request.
            amount: Amount of resource to request.
        
        Returns:
            True if resource was allocated, False otherwise.
        """
        # In a real implementation, this would request resources from the Kernel Runtime
        # For now, just return True
        return True

    async def release_resource(self, resource_type: str, amount: int) -> bool:
        """
        Release resources back to the kernel.
        
        Args:
            resource_type: Type of resource to release.
            amount: Amount of resource to release.
        
        Returns:
            True if resource was released, False otherwise.
        """
        # In a real implementation, this would release resources to the Kernel Runtime
        # For now, just return True
        return True

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the kernel integration.
        
        Returns:
            Dictionary with kernel integration information.
        """
        return {
            "status": "active" if self._initialized and self._started and self._registered else "inactive",
            "registered": self._registered,
            "metrics": self._metrics.to_dict(),
            "kernel_status": await self.get_kernel_status() if self._registered else {},
        }

    async def reset(self) -> None:
        """
        Reset the kernel integration.
        
        This method resets all state and unregisters from the kernel.
        """
        logger.info("Resetting KernelIntegration...")
        
        await self.unregister()
        
        self._metrics = KernelIntegrationMetrics()
        self._initialized = False
        self._started = False
        self._registered = False
        
        logger.info("KernelIntegration reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"KernelIntegration("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"registered={self._registered})"
        )
