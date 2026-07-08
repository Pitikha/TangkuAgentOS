"""
Runtime Communication Framework - Runtime Status Manager

The RuntimeStatusManager provides status tracking and management for
TangkuAgentOS runtimes. It enables:
- Runtime status tracking
- Status history
- Status change notifications
- Status-based filtering
- Status metrics

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.services.registry import (
        RuntimeRegistry,
        RuntimeInfo,
        RuntimeStatus,
    )

logger = logging.getLogger(__name__)


@dataclass
class StatusChange:
    """
    Represents a change in runtime status.

    Attributes:
        runtime_id: ID of the runtime.
        old_status: Previous status.
        new_status: New status.
        timestamp: When the change occurred.
        reason: Reason for the status change.
        metadata: Additional metadata about the change.
    """

    runtime_id: str
    old_status: str
    new_status: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class RuntimeStatusInfo:
    """
    Comprehensive status information for a runtime.

    Attributes:
        runtime_id: ID of the runtime.
        current_status: Current status.
        previous_status: Previous status.
        status_history: History of status changes.
        last_changed: When the status last changed.
        uptime: How long the runtime has been in the current status.
        total_uptime: Total time the runtime has been running.
        start_count: Number of times the runtime has been started.
        stop_count: Number of times the runtime has been stopped.
        error_count: Number of times the runtime has failed.
        metadata: Additional status metadata.
    """

    runtime_id: str
    current_status: str
    previous_status: Optional[str] = None
    status_history: List[StatusChange] = field(default_factory=list)
    last_changed: Optional[datetime] = None
    uptime: float = 0.0
    total_uptime: float = 0.0
    start_count: int = 0
    stop_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "current_status": self.current_status,
            "previous_status": self.previous_status,
            "last_changed": self.last_changed.isoformat() if self.last_changed else None,
            "uptime": self.uptime,
            "total_uptime": self.total_uptime,
            "start_count": self.start_count,
            "stop_count": self.stop_count,
            "error_count": self.error_count,
            "metadata": self.metadata,
        }


class RuntimeStatusManager:
    """
    Status manager for TangkuAgentOS runtimes.

    The RuntimeStatusManager provides comprehensive status tracking and
    management for runtimes. It tracks status changes over time and
    provides metrics and notifications for status transitions.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.status import RuntimeStatusManager
        >>> from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
        >>> 
        >>> registry = RuntimeRegistry()
        >>> status_manager = RuntimeStatusManager(registry)
        >>> 
        >>> # Register a runtime
        >>> registry.register("memory_runtime", name="Memory Runtime")
        >>> 
        >>> # Get status
        >>> status = status_manager.get_status("memory_runtime")
        >>> status.current_status
        'registered'

    Attributes:
        registry: Runtime registry to monitor.
    """

    def __init__(
        self,
        registry: Optional["RuntimeRegistry"] = None,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime status manager.

        Args:
            registry: Runtime registry to monitor.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        self._registry = registry
        self._owns_registry = registry is None

        if self._registry is None:
            from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry

            self._registry = RuntimeRegistry()

        # Status info: runtime_id -> RuntimeStatusInfo
        self._status_info: Dict[str, RuntimeStatusInfo] = {}
        self._status_info_lock = asyncio.Lock()

        # Status change callbacks
        self._on_status_change: List[Callable[[str, str, str, Dict[str, Any]], None]] = []

        # Status history limit
        self._max_history = 1000

        # Metrics
        self._metrics: Dict[str, Any] = {
            "status_changes": 0,
            "runtimes_started": 0,
            "runtimes_stopped": 0,
            "runtimes_failed": 0,
            "status_queries": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        # Register with registry for status change notifications
        self._registry.on_status_change(self._handle_registry_status_change)

        logger.info("RuntimeStatusManager initialized")

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        return self._registry

    def get_status(self, runtime_id: str) -> Optional[RuntimeStatusInfo]:
        """
        Get the status information for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            RuntimeStatusInfo if found, None otherwise.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> status = status_manager.get_status("memory_runtime")
        """
        async with self._status_info_lock:
            return self._status_info.get(runtime_id)

    def get_current_status(self, runtime_id: str) -> Optional[str]:
        """
        Get the current status of a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Current status string or None if not found.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> status = status_manager.get_current_status("memory_runtime")
        """
        info = self.get_status(runtime_id)
        if info:
            return info.current_status
        return None

    def get_status_history(
        self,
        runtime_id: str,
        limit: int = 100,
    ) -> List[StatusChange]:
        """
        Get the status change history for a runtime.

        Args:
            runtime_id: ID of the runtime.
            limit: Maximum number of changes to return.

        Returns:
            List of status changes.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> history = status_manager.get_status_history("memory_runtime")
        """
        info = self.get_status(runtime_id)
        if info:
            return info.status_history[-limit:]
        return []

    def set_status(
        self,
        runtime_id: str,
        new_status: str,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set the status of a runtime.

        Args:
            runtime_id: ID of the runtime.
            new_status: New status.
            reason: Reason for the status change.
            metadata: Additional metadata.

        Returns:
            True if status was updated, False otherwise.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> status_manager.set_status("memory_runtime", "running")
            True
        """
        return asyncio.run(
            self._set_status_async(runtime_id, new_status, reason, metadata)
        )

    async def _set_status_async(
        self,
        runtime_id: str,
        new_status: str,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Async version of set_status."""
        # Get runtime info from registry
        runtime_info = self._registry.get(runtime_id)
        if runtime_info is None:
            return False

        async with self._status_info_lock:
            # Initialize status info if not exists
            if runtime_id not in self._status_info:
                self._status_info[runtime_id] = RuntimeStatusInfo(
                    runtime_id=runtime_id,
                    current_status=runtime_info.status.value,
                )

            info = self._status_info[runtime_id]
            old_status = info.current_status

            # Skip if status hasn't changed
            if old_status == new_status:
                return False

            # Create status change record
            change = StatusChange(
                runtime_id=runtime_id,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
                metadata=metadata or {},
            )

            # Update status info
            info.previous_status = old_status
            info.current_status = new_status
            info.last_changed = datetime.utcnow()
            info.status_history.append(change)

            # Trim history if too long
            if len(info.status_history) > self._max_history:
                info.status_history = info.status_history[-self._max_history:]

            # Update counters based on status transitions
            if new_status == "running":
                info.start_count += 1
                async with self._metrics_lock:
                    self._metrics["runtimes_started"] += 1
            elif new_status in ("stopped", "stopping"):
                info.stop_count += 1
                async with self._metrics_lock:
                    self._metrics["runtimes_stopped"] += 1
            elif new_status in ("failed", "unhealthy"):
                info.error_count += 1
                async with self._metrics_lock:
                    self._metrics["runtimes_failed"] += 1

            # Update metrics
            async with self._metrics_lock:
                self._metrics["status_changes"] += 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, new_status, change.metadata)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(
                    f"Status changed: {runtime_id} {old_status} -> {new_status} "
                    f"(reason: {reason})"
                )

            return True

    def update_uptime(self, runtime_id: str) -> None:
        """
        Update uptime for a runtime.

        This should be called periodically to update the uptime counters.

        Args:
            runtime_id: ID of the runtime.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> status_manager.update_uptime("memory_runtime")
        """
        asyncio.run(self._update_uptime_async(runtime_id))

    async def _update_uptime_async(self, runtime_id: str) -> None:
        """Async version of update_uptime."""
        async with self._status_info_lock:
            if runtime_id not in self._status_info:
                return

            info = self._status_info[runtime_id]
            now = datetime.utcnow()

            # Update uptime for current status
            if info.last_changed:
                info.uptime = (now - info.last_changed).total_seconds()

            # Update total uptime if running
            if info.current_status == "running":
                info.total_uptime += info.uptime

    def on_status_change(
        self,
        callback: Callable[[str, str, str, Dict[str, Any]], None],
    ) -> None:
        """
        Register a callback for status changes.

        Args:
            callback: Callback function to call when a runtime's status changes.
                     Parameters: (runtime_id, old_status, new_status, metadata)

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> def on_change(runtime_id, old_status, new_status, metadata):
            ...     print(f"Status changed: {runtime_id} {old_status} -> {new_status}")
            >>> status_manager.on_status_change(on_change)
        """
        self._on_status_change.append(callback)

    def get_runtimes_by_status(self, status: str) -> List[str]:
        """
        Get all runtime IDs with a specific status.

        Args:
            status: Status to filter by.

        Returns:
            List of runtime IDs.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> runtimes = status_manager.get_runtimes_by_status("running")
        """
        result = []
        for runtime_id, info in self._status_info.items():
            if info.current_status == status:
                result.append(runtime_id)
        return result

    def get_status_counts(self) -> Dict[str, int]:
        """
        Get counts of runtimes by status.

        Returns:
            Dictionary mapping status to count.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> counts = status_manager.get_status_counts()
            >>> counts["running"]
            0
        """
        counts: Dict[str, int] = defaultdict(int)
        for info in self._status_info.values():
            counts[info.current_status] += 1
        return dict(counts)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get status manager metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> metrics = status_manager.get_metrics()
            >>> metrics["status_changes"]
            0
        """
        return {
            **self._metrics,
            "runtimes_tracked": len(self._status_info),
            "status_counts": self.get_status_counts(),
        }

    def clear(self) -> int:
        """
        Clear all status data.

        Returns:
            Number of runtimes cleared.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> count = status_manager.clear()
        """
        count = len(self._status_info)
        self._status_info.clear()
        self._metrics = {
            "status_changes": 0,
            "runtimes_started": 0,
            "runtimes_stopped": 0,
            "runtimes_failed": 0,
            "status_queries": 0,
        }
        return count

    def shutdown(self) -> None:
        """
        Shutdown the status manager.

        Example:
            >>> status_manager = RuntimeStatusManager()
            >>> status_manager.shutdown()
        """
        self.clear()
        self._on_status_change.clear()

        if self._owns_registry:
            self._registry.shutdown()

        logger.info("Runtime status manager shutdown complete")

    def _handle_registry_status_change(
        self,
        runtime_id: str,
        old_status: "RuntimeStatus",
        new_status: "RuntimeStatus",
    ) -> None:
        """
        Handle status changes from the registry.

        Args:
            runtime_id: ID of the runtime.
            old_status: Previous status.
            new_status: New status.
        """
        # Update our status info to match the registry
        asyncio.run(
            self._set_status_async(
                runtime_id,
                new_status.value,
                f"Registry status change: {old_status.value} -> {new_status.value}",
            )
        )

    def __repr__(self) -> str:
        """Return string representation of the status manager."""
        return (
            f"RuntimeStatusManager("
            f"tracked={len(self._status_info)}, "
            f"changes={self._metrics['status_changes']})"
        )
