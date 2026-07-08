"""
Runtime Communication Framework - Runtime Integration Registry

This module provides the RuntimeIntegrationRegistry which tracks all runtimes
that have been integrated with the Runtime Communication Framework.

The registry:
- Tracks all integrated runtimes
- Manages runtime lifecycle
- Provides discovery capabilities
- Handles runtime registration and unregistration
- Maintains runtime metadata and capabilities

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.integration.base import BaseRuntime
    from tangku_agentos.runtime_communication.buses import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
        BroadcastBus,
        RequestResponseBus,
    )

logger = logging.getLogger(__name__)


class RuntimeIntegrationStatus(Enum):
    """
    Status of a runtime integration.

    Attributes:
        PENDING: Runtime is pending integration.
        INTEGRATING: Runtime is being integrated.
        INTEGRATED: Runtime is fully integrated.
        DEGRADED: Runtime is integrated but with issues.
        FAILED: Integration failed.
        UNINTEGRATING: Runtime is being unintegrated.
        UNINTEGRATED: Runtime is not integrated.
    """

    PENDING = auto()
    INTEGRATING = auto()
    INTEGRATED = auto()
    DEGRADED = auto()
    FAILED = auto()
    UNINTEGRATING = auto()
    UNINTEGRATED = auto()


@dataclass
class RuntimeIntegrationInfo:
    """
    Information about a runtime integration.

    Attributes:
        runtime_id: Unique ID of the runtime.
        name: Human-readable name.
        type: Type of the runtime.
        version: Runtime version.
        status: Current integration status.
        registered_at: When the runtime was registered.
        integrated_at: When the runtime was integrated.
        last_heartbeat: Last heartbeat timestamp.
        capabilities: Set of runtime capabilities.
        dependencies: List of runtime dependencies.
        metadata: Runtime metadata.
        integration_metadata: Integration-specific metadata.
        error: Last error if integration failed.
    """

    runtime_id: str
    name: str
    type: str
    version: str = "1.0.0"
    status: RuntimeIntegrationStatus = RuntimeIntegrationStatus.PENDING
    registered_at: datetime = field(default_factory=datetime.utcnow)
    integrated_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    capabilities: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    integration_metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def is_integrated(self) -> bool:
        """Check if the runtime is integrated."""
        return self.status == RuntimeIntegrationStatus.INTEGRATED

    def is_available(self) -> bool:
        """Check if the runtime is available."""
        return self.status in (
            RuntimeIntegrationStatus.INTEGRATED,
            RuntimeIntegrationStatus.DEGRADED,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "status": self.status.name,
            "registered_at": self.registered_at.isoformat(),
            "integrated_at": self.integrated_at.isoformat() if self.integrated_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "capabilities": list(self.capabilities),
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "integration_metadata": self.integration_metadata,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeIntegrationInfo":
        """Create from dictionary."""
        return cls(
            runtime_id=data["runtime_id"],
            name=data["name"],
            type=data["type"],
            version=data.get("version", "1.0.0"),
            status=RuntimeIntegrationStatus[data.get("status", "PENDING")],
            registered_at=datetime.fromisoformat(data["registered_at"]),
            integrated_at=datetime.fromisoformat(data["integrated_at"])
            if data.get("integrated_at")
            else None,
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"])
            if data.get("last_heartbeat")
            else None,
            capabilities=set(data.get("capabilities", [])),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            integration_metadata=data.get("integration_metadata", {}),
            error=data.get("error"),
        )


class RuntimeIntegrationRegistry:
    """
    Registry for tracking runtime integrations with the Runtime Communication Framework.

    This registry maintains information about all runtimes that have been
    integrated with the framework, including their status, capabilities, and metadata.

    The registry provides:
    - Runtime registration and unregistration
    - Runtime discovery by various criteria
    - Runtime status tracking
    - Heartbeat monitoring
    - Integration lifecycle management

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.registry import (
        ...     RuntimeIntegrationRegistry,
        ... )
        >>> 
        >>> registry = RuntimeIntegrationRegistry()
        >>> 
        >>> # Register a runtime
        >>> await registry.register(
        ...     runtime_id="memory_runtime",
        ...     name="Memory Runtime",
        ...     type="memory",
        ...     capabilities={"memory", "storage"}
        ... )
        >>> 
        >>> # Discover runtimes by capability
        >>> runtimes = registry.discover_by_capability("memory")
        >>> 
        >>> # Get runtime info
        >>> info = registry.get("memory_runtime")
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        heartbeat_timeout: float = 60.0,
        enable_monitoring: bool = True,
    ):
        """
        Initialize the runtime integration registry.

        Args:
            heartbeat_interval: Interval between heartbeats in seconds.
            heartbeat_timeout: Timeout for heartbeat in seconds.
            enable_monitoring: Whether to enable heartbeat monitoring.
        """
        self._runtimes: Dict[str, RuntimeIntegrationInfo] = {}
        self._lock = asyncio.Lock()

        # Heartbeat tracking
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._enable_monitoring = enable_monitoring
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}

        # Callbacks
        self._on_register: List[Callable[[RuntimeIntegrationInfo], None]] = []
        self._on_unregister: List[Callable[[RuntimeIntegrationInfo], None]] = []
        self._on_status_change: List[Callable[[RuntimeIntegrationInfo, RuntimeIntegrationStatus], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "total_runtimes": 0,
            "integrated_runtimes": 0,
            "pending_runtimes": 0,
            "failed_runtimes": 0,
            "registrations": 0,
            "unregistrations": 0,
            "heartbeats": 0,
            "timeouts": 0,
        }

        logger.info(
            f"RuntimeIntegrationRegistry initialized "
            f"(heartbeat_interval={heartbeat_interval}, "
            f"heartbeat_timeout={heartbeat_timeout})"
        )

    async def register(
        self,
        runtime_id: str,
        name: str,
        type: str,
        version: str = "1.0.0",
        capabilities: Optional[Set[str]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        integration_metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeIntegrationInfo:
        """
        Register a runtime with the integration registry.

        Args:
            runtime_id: Unique ID of the runtime.
            name: Human-readable name.
            type: Type of the runtime.
            version: Runtime version.
            capabilities: Set of runtime capabilities.
            dependencies: List of runtime dependencies.
            metadata: Runtime metadata.
            integration_metadata: Integration-specific metadata.

        Returns:
            Runtime integration info.

        Raises:
            ValueError: If runtime is already registered.
        """
        async with self._lock:
            if runtime_id in self._runtimes:
                existing = self._runtimes[runtime_id]
                if existing.status == RuntimeIntegrationStatus.UNINTEGRATED:
                    # Allow re-registration after unregistration
                    pass
                else:
                    raise ValueError(f"Runtime already registered: {runtime_id}")

            info = RuntimeIntegrationInfo(
                runtime_id=runtime_id,
                name=name,
                type=type,
                version=version,
                status=RuntimeIntegrationStatus.INTEGRATING,
                capabilities=capabilities or set(),
                dependencies=dependencies or [],
                metadata=metadata or {},
                integration_metadata=integration_metadata or {},
            )

            self._runtimes[runtime_id] = info
            self._metrics["total_runtimes"] += 1
            self._metrics["registrations"] += 1

            # Update status to INTEGRATED
            info.status = RuntimeIntegrationStatus.INTEGRATED
            info.integrated_at = datetime.utcnow()
            self._metrics["integrated_runtimes"] += 1

            # Start heartbeat monitoring if enabled
            if self._enable_monitoring:
                self._start_heartbeat(runtime_id)

            # Call callbacks
            for callback in self._on_register:
                try:
                    callback(info)
                except Exception as e:
                    logger.error(f"Error in register callback: {e}")

            logger.info(f"Runtime registered: {runtime_id} ({name})")
            return info

    async def unregister(self, runtime_id: str) -> Optional[RuntimeIntegrationInfo]:
        """
        Unregister a runtime from the integration registry.

        Args:
            runtime_id: ID of the runtime to unregister.

        Returns:
            Runtime integration info if found, None otherwise.
        """
        async with self._lock:
            if runtime_id not in self._runtimes:
                return None

            info = self._runtimes[runtime_id]

            # Stop heartbeat monitoring
            if self._enable_monitoring:
                self._stop_heartbeat(runtime_id)

            # Update status
            info.status = RuntimeIntegrationStatus.UNINTEGRATED
            self._metrics["integrated_runtimes"] -= 1
            self._metrics["unregistrations"] += 1

            # Remove from registry
            del self._runtimes[runtime_id]
            self._metrics["total_runtimes"] -= 1

            # Call callbacks
            for callback in self._on_unregister:
                try:
                    callback(info)
                except Exception as e:
                    logger.error(f"Error in unregister callback: {e}")

            logger.info(f"Runtime unregistered: {runtime_id}")
            return info

    async def update_status(
        self,
        runtime_id: str,
        new_status: RuntimeIntegrationStatus,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a runtime integration.

        Args:
            runtime_id: ID of the runtime.
            new_status: New status.
            error: Error message if status is FAILED.

        Returns:
            True if status was updated, False if runtime not found.
        """
        async with self._lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if old_status == new_status:
                return False

            info.status = new_status
            info.error = error

            # Update metrics
            if old_status == RuntimeIntegrationStatus.INTEGRATED:
                self._metrics["integrated_runtimes"] -= 1
            if new_status == RuntimeIntegrationStatus.INTEGRATED:
                self._metrics["integrated_runtimes"] += 1

            # Call callbacks
            for callback in self._on_status_change:
                try:
                    callback(info, new_status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            logger.info(f"Runtime status changed: {runtime_id} {old_status.name} -> {new_status.name}")
            return True

    async def update_heartbeat(self, runtime_id: str) -> bool:
        """
        Update the heartbeat for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if heartbeat was updated, False if runtime not found.
        """
        async with self._lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            info.last_heartbeat = datetime.utcnow()
            self._metrics["heartbeats"] += 1

            logger.debug(f"Runtime heartbeat: {runtime_id}")
            return True

    def _start_heartbeat(self, runtime_id: str) -> None:
        """Start heartbeat monitoring for a runtime."""
        async def heartbeat_loop():
            while True:
                try:
                    await asyncio.sleep(self._heartbeat_interval)
                    async with self._lock:
                        if runtime_id not in self._runtimes:
                            break
                        info = self._runtimes[runtime_id]
                        if info.last_heartbeat:
                            elapsed = (datetime.utcnow() - info.last_heartbeat).total_seconds()
                            if elapsed > self._heartbeat_timeout:
                                # Mark as timed out
                                info.status = RuntimeIntegrationStatus.DEGRADED
                                self._metrics["timeouts"] += 1
                                logger.warning(
                                    f"Runtime heartbeat timeout: {runtime_id} "
                                    f"(last heartbeat: {elapsed}s ago)"
                                )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in heartbeat loop for {runtime_id}: {e}")

        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[runtime_id] = task

    def _stop_heartbeat(self, runtime_id: str) -> None:
        """Stop heartbeat monitoring for a runtime."""
        if runtime_id in self._heartbeat_tasks:
            task = self._heartbeat_tasks.pop(runtime_id)
            task.cancel()

    def get(self, runtime_id: str) -> Optional[RuntimeIntegrationInfo]:
        """
        Get runtime integration info by ID.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Runtime integration info if found, None otherwise.
        """
        return self._runtimes.get(runtime_id)

    def list_all(self) -> List[RuntimeIntegrationInfo]:
        """
        List all registered runtimes.

        Returns:
            List of all runtime integration infos.
        """
        return list(self._runtimes.values())

    def list_by_status(self, status: RuntimeIntegrationStatus) -> List[RuntimeIntegrationInfo]:
        """
        List runtimes by status.

        Args:
            status: Status to filter by.

        Returns:
            List of runtime integration infos with the given status.
        """
        return [info for info in self._runtimes.values() if info.status == status]

    def list_by_type(self, runtime_type: str) -> List[RuntimeIntegrationInfo]:
        """
        List runtimes by type.

        Args:
            runtime_type: Type to filter by.

        Returns:
            List of runtime integration infos with the given type.
        """
        return [info for info in self._runtimes.values() if info.type == runtime_type]

    def list_by_capability(self, capability: str) -> List[RuntimeIntegrationInfo]:
        """
        List runtimes that have a specific capability.

        Args:
            capability: Capability to filter by.

        Returns:
            List of runtime integration infos with the given capability.
        """
        return [
            info for info in self._runtimes.values()
            if capability in info.capabilities
        ]

    def discover(
        self,
        type: Optional[str] = None,
        capability: Optional[str] = None,
        status: Optional[RuntimeIntegrationStatus] = None,
        name_contains: Optional[str] = None,
    ) -> List[RuntimeIntegrationInfo]:
        """
        Discover runtimes matching the given criteria.

        Args:
            type: Runtime type to filter by.
            capability: Capability to filter by.
            status: Status to filter by.
            name_contains: String to search for in runtime names.

        Returns:
            List of matching runtime integration infos.
        """
        results = []
        for info in self._runtimes.values():
            if type and info.type != type:
                continue
            if capability and capability not in info.capabilities:
                continue
            if status and info.status != status:
                continue
            if name_contains and name_contains.lower() not in info.name.lower():
                continue
            results.append(info)
        return results

    def has_capability(self, runtime_id: str, capability: str) -> bool:
        """
        Check if a runtime has a specific capability.

        Args:
            runtime_id: ID of the runtime.
            capability: Capability to check.

        Returns:
            True if the runtime has the capability, False otherwise.
        """
        info = self._runtimes.get(runtime_id)
        return info is not None and capability in info.capabilities

    def get_capabilities(self, runtime_id: str) -> Set[str]:
        """
        Get the capabilities of a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Set of capabilities, or empty set if runtime not found.
        """
        info = self._runtimes.get(runtime_id)
        return info.capabilities if info else set()

    def get_dependencies(self, runtime_id: str) -> List[str]:
        """
        Get the dependencies of a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            List of dependencies, or empty list if runtime not found.
        """
        info = self._runtimes.get(runtime_id)
        return info.dependencies if info else []

    def is_registered(self, runtime_id: str) -> bool:
        """
        Check if a runtime is registered.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if the runtime is registered, False otherwise.
        """
        return runtime_id in self._runtimes

    def is_integrated(self, runtime_id: str) -> bool:
        """
        Check if a runtime is integrated.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if the runtime is integrated, False otherwise.
        """
        info = self._runtimes.get(runtime_id)
        return info is not None and info.is_integrated()

    def is_available(self, runtime_id: str) -> bool:
        """
        Check if a runtime is available.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if the runtime is available, False otherwise.
        """
        info = self._runtimes.get(runtime_id)
        return info is not None and info.is_available()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get registry metrics.

        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "runtime_count": len(self._runtimes),
            "integrated_count": len(self.list_by_status(RuntimeIntegrationStatus.INTEGRATED)),
            "pending_count": len(self.list_by_status(RuntimeIntegrationStatus.PENDING)),
            "failed_count": len(self.list_by_status(RuntimeIntegrationStatus.FAILED)),
        }

    def on_register(self, callback: Callable[[RuntimeIntegrationInfo], None]) -> None:
        """
        Register a callback for runtime registration.

        Args:
            callback: Callback function.
        """
        self._on_register.append(callback)

    def on_unregister(self, callback: Callable[[RuntimeIntegrationInfo], None]) -> None:
        """
        Register a callback for runtime unregistration.

        Args:
            callback: Callback function.
        """
        self._on_unregister.append(callback)

    def on_status_change(
        self,
        callback: Callable[[RuntimeIntegrationInfo, RuntimeIntegrationStatus], None],
    ) -> None:
        """
        Register a callback for runtime status changes.

        Args:
            callback: Callback function.
        """
        self._on_status_change.append(callback)

    def clear(self) -> int:
        """
        Clear all registrations.

        Returns:
            Number of runtimes cleared.
        """
        async def clear_async():
            count = len(self._runtimes)
            for runtime_id in list(self._runtimes.keys()):
                await self.unregister(runtime_id)
            return count

        return asyncio.run(clear_async())

    def shutdown(self) -> None:
        """Shutdown the registry."""
        # Stop all heartbeat tasks
        for runtime_id, task in self._heartbeat_tasks.items():
            task.cancel()
        self._heartbeat_tasks.clear()

        # Clear all registrations
        self._runtimes.clear()
        self._metrics = {
            "total_runtimes": 0,
            "integrated_runtimes": 0,
            "pending_runtimes": 0,
            "failed_runtimes": 0,
            "registrations": 0,
            "unregistrations": 0,
            "heartbeats": 0,
            "timeouts": 0,
        }

        logger.info("RuntimeIntegrationRegistry shutdown complete")

    def __len__(self) -> int:
        """Get the number of registered runtimes."""
        return len(self._runtimes)

    def __contains__(self, runtime_id: str) -> bool:
        """Check if a runtime is registered."""
        return runtime_id in self._runtimes

    def __iter__(self):
        """Iterate over registered runtime IDs."""
        return iter(self._runtimes.keys())

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RuntimeIntegrationRegistry("
            f"runtimes={len(self._runtimes)}, "
            f"integrated={len(self.list_by_status(RuntimeIntegrationStatus.INTEGRATED))})"
        )
