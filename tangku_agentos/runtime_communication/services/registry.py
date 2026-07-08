"""
Runtime Communication Framework - Runtime Registry Service

The RuntimeRegistry provides a centralized registry for all runtimes in
TangkuAgentOS. It enables:
- Runtime registration and unregistration
- Runtime lookup by ID or type
- Runtime metadata management
- Runtime capability discovery
- Runtime lifecycle tracking

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
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Message

logger = logging.getLogger(__name__)


class RuntimeStatus(Enum):
    """
    Status of a runtime.

    Attributes:
        REGISTERED: Runtime has been registered but not yet started.
        STARTING: Runtime is starting up.
        RUNNING: Runtime is running normally.
        PAUSED: Runtime is paused.
        STOPPING: Runtime is stopping.
        STOPPED: Runtime has been stopped.
        FAILED: Runtime has failed.
        UNRESPONSIVE: Runtime is not responding to health checks.
        DEGRADED: Runtime is running but with issues.
    """

    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNRESPONSIVE = "unresponsive"
    DEGRADED = "degraded"


@dataclass
class RuntimeInfo:
    """
    Information about a registered runtime.

    Attributes:
        runtime_id: Unique identifier for the runtime.
        name: Human-readable name for the runtime.
        type: Type of runtime (e.g., "memory", "kernel", "provider").
        status: Current status of the runtime.
        version: Version of the runtime.
        description: Description of the runtime.
        capabilities: Set of capabilities provided by the runtime.
        dependencies: List of runtime IDs this runtime depends on.
        metadata: Additional runtime metadata.
        created_at: When the runtime was registered.
        started_at: When the runtime was started.
        stopped_at: When the runtime was stopped.
        last_heartbeat: Last heartbeat timestamp.
        endpoint: Runtime endpoint URL (if applicable).
        health_check_url: Health check endpoint URL (if applicable).
    """

    runtime_id: str
    name: str
    type: str
    status: RuntimeStatus = RuntimeStatus.REGISTERED
    version: str = "1.0.0"
    description: str = ""
    capabilities: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    endpoint: Optional[str] = None
    health_check_url: Optional[str] = None

    def add_capability(self, capability: str) -> None:
        """Add a capability to the runtime."""
        self.capabilities.add(capability)

    def add_capabilities(self, capabilities: Set[str]) -> None:
        """Add multiple capabilities to the runtime."""
        self.capabilities.update(capabilities)

    def remove_capability(self, capability: str) -> bool:
        """Remove a capability from the runtime."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            return True
        return False

    def has_capability(self, capability: str) -> bool:
        """Check if the runtime has a specific capability."""
        return capability in self.capabilities

    def is_running(self) -> bool:
        """Check if the runtime is running."""
        return self.status == RuntimeStatus.RUNNING

    def is_available(self) -> bool:
        """Check if the runtime is available (running or starting)."""
        return self.status in (RuntimeStatus.RUNNING, RuntimeStatus.STARTING)

    def to_dict(self) -> Dict[str, Any]:
        """Convert runtime info to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "type": self.type,
            "status": self.status.value,
            "version": self.version,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "dependencies": list(self.dependencies),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "endpoint": self.endpoint,
            "health_check_url": self.health_check_url,
        }


@dataclass
class RuntimeRegistrationOptions:
    """
    Options for runtime registration.

    Attributes:
        name: Human-readable name for the runtime.
        type: Type of runtime.
        version: Version of the runtime.
        description: Description of the runtime.
        capabilities: Set of capabilities provided by the runtime.
        dependencies: List of runtime IDs this runtime depends on.
        metadata: Additional runtime metadata.
        endpoint: Runtime endpoint URL.
        health_check_url: Health check endpoint URL.
        auto_start: Whether to automatically start the runtime.
    """

    name: str = ""
    type: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    endpoint: Optional[str] = None
    health_check_url: Optional[str] = None
    auto_start: bool = False


class RuntimeRegistry:
    """
    Central registry for all runtimes in TangkuAgentOS.

    The RuntimeRegistry provides a centralized way to register, discover,
    and manage runtimes. It enables loose coupling between runtimes by
    allowing them to discover each other without direct dependencies.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
        >>> 
        >>> registry = RuntimeRegistry()
        >>> 
        >>> # Register a runtime
        >>> runtime_id = registry.register(
        ...     "memory_runtime",
        ...     name="Memory Runtime",
        ...     type="memory",
        ...     capabilities={"storage", "retrieval"}
        ... )
        >>> 
        >>> # Get runtime info
        >>> info = registry.get("memory_runtime")
        >>> info.name
        'Memory Runtime'
        >>> 
        >>> # Find runtimes by capability
        >>> runtimes = registry.find_by_capability("storage")

    Attributes:
        max_runtimes: Maximum number of runtimes that can be registered.
    """

    def __init__(
        self,
        max_runtimes: int = 10000,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime registry.

        Args:
            max_runtimes: Maximum number of runtimes that can be registered.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Runtime storage: runtime_id -> RuntimeInfo
        self._runtimes: Dict[str, RuntimeInfo] = {}
        self._runtimes_lock = asyncio.Lock()
        self._max_runtimes = max_runtimes

        # Indexes for fast lookup
        self._by_name: Dict[str, str] = {}  # name -> runtime_id
        self._by_type: Dict[str, Set[str]] = defaultdict(set)  # type -> Set[runtime_id]
        self._by_capability: Dict[str, Set[str]] = defaultdict(set)  # capability -> Set[runtime_id]
        self._indexes_lock = asyncio.Lock()

        # Registration callbacks
        self._on_register: List[Callable[[str, RuntimeInfo], None]] = []
        self._on_unregister: List[Callable[[str, RuntimeInfo], None]] = []
        self._on_status_change: List[Callable[[str, RuntimeStatus, RuntimeStatus], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "runtimes_registered": 0,
            "runtimes_unregistered": 0,
            "runtimes_running": 0,
            "runtimes_failed": 0,
            "registrations_rejected": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(f"RuntimeRegistry initialized with max_runtimes={max_runtimes}")

    def register(
        self,
        runtime_id: str,
        name: Optional[str] = None,
        type: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        capabilities: Optional[Set[str]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        health_check_url: Optional[str] = None,
        auto_start: bool = False,
    ) -> str:
        """
        Register a runtime.

        Args:
            runtime_id: Unique identifier for the runtime.
            name: Human-readable name for the runtime.
            type: Type of runtime.
            version: Version of the runtime.
            description: Description of the runtime.
            capabilities: Set of capabilities provided by the runtime.
            dependencies: List of runtime IDs this runtime depends on.
            metadata: Additional runtime metadata.
            endpoint: Runtime endpoint URL.
            health_check_url: Health check endpoint URL.
            auto_start: Whether to automatically start the runtime.

        Returns:
            Runtime ID.

        Raises:
            RuntimeError: If maximum number of runtimes is reached.

        Example:
            >>> registry = RuntimeRegistry()
            >>> runtime_id = registry.register(
            ...     "memory_runtime",
            ...     name="Memory Runtime",
            ...     type="memory",
            ...     capabilities={"storage", "retrieval"}
            ... )
        """
        return asyncio.run(
            self._register_async(
                runtime_id,
                name,
                type,
                version,
                description,
                capabilities,
                dependencies,
                metadata,
                endpoint,
                health_check_url,
                auto_start,
            )
        )

    async def _register_async(
        self,
        runtime_id: str,
        name: Optional[str] = None,
        type: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        capabilities: Optional[Set[str]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        health_check_url: Optional[str] = None,
        auto_start: bool = False,
    ) -> str:
        """Async version of register."""
        # Check if we're at capacity
        async with self._runtimes_lock:
            if len(self._runtimes) >= self._max_runtimes:
                async with self._metrics_lock:
                    self._metrics["registrations_rejected"] += 1

                from tangku_agentos.runtime_communication.models.exceptions import (
                    RuntimeNotFoundError,
                )

                raise RuntimeError(
                    f"Maximum number of runtimes ({self._max_runtimes}) reached"
                )

            # Use provided runtime_id or generate one
            if not runtime_id:
                runtime_id = str(uuid.uuid4())

            # Check if runtime already exists
            if runtime_id in self._runtimes:
                if self._enable_logging:
                    logger.warning(f"Runtime already registered: {runtime_id}")
                return runtime_id

            # Create runtime info
            info = RuntimeInfo(
                runtime_id=runtime_id,
                name=name or runtime_id,
                type=type or "unknown",
                version=version,
                description=description,
                capabilities=capabilities or set(),
                dependencies=dependencies or [],
                metadata=metadata or {},
                endpoint=endpoint,
                health_check_url=health_check_url,
            )

            # Store runtime
            self._runtimes[runtime_id] = info

            # Update indexes
            async with self._indexes_lock:
                self._by_name[info.name] = runtime_id
                self._by_type[info.type].add(runtime_id)
                for capability in info.capabilities:
                    self._by_capability[capability].add(runtime_id)

            # Update metrics
            async with self._metrics_lock:
                self._metrics["runtimes_registered"] += 1
                if info.status == RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] += 1

            # If auto_start, start the runtime
            if auto_start:
                await self.start(runtime_id)

            # Call registration callbacks
            for callback in self._on_register:
                try:
                    callback(runtime_id, info)
                except Exception as e:
                    logger.error(f"Error in registration callback: {e}")

            if self._enable_logging:
                logger.info(
                    f"Runtime registered: {runtime_id} ({info.name}, type={info.type})"
                )

        return runtime_id

    def register_with_options(
        self,
        runtime_id: str,
        options: RuntimeRegistrationOptions,
    ) -> str:
        """
        Register a runtime with options.

        Args:
            runtime_id: Unique identifier for the runtime.
            options: Registration options.

        Returns:
            Runtime ID.

        Example:
            >>> registry = RuntimeRegistry()
            >>> options = RuntimeRegistrationOptions(
            ...     name="Memory Runtime",
            ...     type="memory",
            ...     capabilities={"storage", "retrieval"}
            ... )
            >>> runtime_id = registry.register_with_options("memory_runtime", options)
        """
        return self.register(
            runtime_id=runtime_id,
            name=options.name,
            type=options.type,
            version=options.version,
            description=options.description,
            capabilities=options.capabilities,
            dependencies=options.dependencies,
            metadata=options.metadata,
            endpoint=options.endpoint,
            health_check_url=options.health_check_url,
            auto_start=options.auto_start,
        )

    def unregister(self, runtime_id: str) -> bool:
        """
        Unregister a runtime.

        Args:
            runtime_id: ID of the runtime to unregister.

        Returns:
            True if runtime was unregistered, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.unregister("memory_runtime")
            True
        """
        return asyncio.run(self._unregister_async(runtime_id))

    async def _unregister_async(self, runtime_id: str) -> bool:
        """Async version of unregister."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]

            # Update indexes
            async with self._indexes_lock:
                if info.name in self._by_name:
                    del self._by_name[info.name]
                if info.type in self._by_type:
                    self._by_type[info.type].discard(runtime_id)
                for capability in info.capabilities:
                    if capability in self._by_capability:
                        self._by_capability[capability].discard(runtime_id)

            # Remove runtime
            del self._runtimes[runtime_id]

            # Update metrics
            async with self._metrics_lock:
                self._metrics["runtimes_unregistered"] += 1
                if info.status == RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] -= 1
                if info.status == RuntimeStatus.FAILED:
                    self._metrics["runtimes_failed"] -= 1

            # Call unregistration callbacks
            for callback in self._on_unregister:
                try:
                    callback(runtime_id, info)
                except Exception as e:
                    logger.error(f"Error in unregistration callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime unregistered: {runtime_id}")

            return True

    def get(self, runtime_id: str) -> Optional[RuntimeInfo]:
        """
        Get information about a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            RuntimeInfo if found, None otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> info = registry.get("memory_runtime")
            >>> info.name
            'Memory Runtime'
        """
        return self._runtimes.get(runtime_id)

    def get_by_name(self, name: str) -> Optional[RuntimeInfo]:
        """
        Get runtime by name.

        Args:
            name: Name of the runtime.

        Returns:
            RuntimeInfo if found, None otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> info = registry.get_by_name("Memory Runtime")
        """
        async with self._indexes_lock:
            runtime_id = self._by_name.get(name)
        if runtime_id:
            return self.get(runtime_id)
        return None

    def list(self) -> List[str]:
        """
        List all registered runtime IDs.

        Returns:
            List of runtime IDs.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.register("kernel_runtime", name="Kernel Runtime")
            >>> registry.list()
            ['memory_runtime', 'kernel_runtime']
        """
        return list(self._runtimes.keys())

    def list_by_type(self, type: str) -> List[str]:
        """
        List all runtime IDs of a specific type.

        Args:
            type: Type of runtime to filter by.

        Returns:
            List of runtime IDs.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime", type="memory")
            >>> registry.register("kernel_runtime", name="Kernel Runtime", type="kernel")
            >>> registry.list_by_type("memory")
            ['memory_runtime']
        """
        async with self._indexes_lock:
            return list(self._by_type.get(type, set()))

    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find all runtime IDs that have a specific capability.

        Args:
            capability: Capability to search for.

        Returns:
            List of runtime IDs.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", capabilities={"storage"})
            >>> registry.register("cache_runtime", capabilities={"storage", "caching"})
            >>> registry.find_by_capability("storage")
            ['memory_runtime', 'cache_runtime']
        """
        async with self._indexes_lock:
            return list(self._by_capability.get(capability, set()))

    def find_by_capabilities(self, capabilities: Set[str]) -> List[str]:
        """
        Find all runtime IDs that have all the specified capabilities.

        Args:
            capabilities: Set of capabilities to search for.

        Returns:
            List of runtime IDs.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", capabilities={"storage"})
            >>> registry.register("cache_runtime", capabilities={"storage", "caching"})
            >>> registry.find_by_capabilities({"storage", "caching"})
            ['cache_runtime']
        """
        async with self._indexes_lock:
            if not capabilities:
                return list(self._runtimes.keys())

            # Find runtimes that have all capabilities
            result = None
            for capability in capabilities:
                if capability in self._by_capability:
                    if result is None:
                        result = set(self._by_capability[capability])
                    else:
                        result &= self._by_capability[capability]
                else:
                    # No runtimes have this capability
                    return []

            return list(result) if result else []

    def start(self, runtime_id: str) -> bool:
        """
        Start a runtime.

        Args:
            runtime_id: ID of the runtime to start.

        Returns:
            True if runtime was started, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.start("memory_runtime")
            True
        """
        return asyncio.run(self._start_async(runtime_id))

    async def _start_async(self, runtime_id: str) -> bool:
        """Async version of start."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if info.status == RuntimeStatus.RUNNING:
                return False

            info.status = RuntimeStatus.RUNNING
            info.started_at = datetime.utcnow()
            info.stopped_at = None

            # Update metrics
            async with self._metrics_lock:
                if old_status != RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] += 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, info.status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime started: {runtime_id}")

            return True

    def stop(self, runtime_id: str) -> bool:
        """
        Stop a runtime.

        Args:
            runtime_id: ID of the runtime to stop.

        Returns:
            True if runtime was stopped, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.start("memory_runtime")
            >>> registry.stop("memory_runtime")
            True
        """
        return asyncio.run(self._stop_async(runtime_id))

    async def _stop_async(self, runtime_id: str) -> bool:
        """Async version of stop."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if info.status not in (
                RuntimeStatus.RUNNING,
                RuntimeStatus.STARTING,
                RuntimeStatus.PAUSED,
            ):
                return False

            info.status = RuntimeStatus.STOPPED
            info.stopped_at = datetime.utcnow()

            # Update metrics
            async with self._metrics_lock:
                if old_status == RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] -= 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, info.status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime stopped: {runtime_id}")

            return True

    def pause(self, runtime_id: str) -> bool:
        """
        Pause a runtime.

        Args:
            runtime_id: ID of the runtime to pause.

        Returns:
            True if runtime was paused, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.start("memory_runtime")
            >>> registry.pause("memory_runtime")
            True
        """
        return asyncio.run(self._pause_async(runtime_id))

    async def _pause_async(self, runtime_id: str) -> bool:
        """Async version of pause."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if info.status != RuntimeStatus.RUNNING:
                return False

            info.status = RuntimeStatus.PAUSED

            # Update metrics
            async with self._metrics_lock:
                self._metrics["runtimes_running"] -= 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, info.status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime paused: {runtime_id}")

            return True

    def resume(self, runtime_id: str) -> bool:
        """
        Resume a paused runtime.

        Args:
            runtime_id: ID of the runtime to resume.

        Returns:
            True if runtime was resumed, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.start("memory_runtime")
            >>> registry.pause("memory_runtime")
            >>> registry.resume("memory_runtime")
            True
        """
        return asyncio.run(self._resume_async(runtime_id))

    async def _resume_async(self, runtime_id: str) -> bool:
        """Async version of resume."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if info.status != RuntimeStatus.PAUSED:
                return False

            info.status = RuntimeStatus.RUNNING

            # Update metrics
            async with self._metrics_lock:
                self._metrics["runtimes_running"] += 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, info.status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime resumed: {runtime_id}")

            return True

    def set_status(
        self, runtime_id: str, status: RuntimeStatus
    ) -> bool:
        """
        Set the status of a runtime.

        Args:
            runtime_id: ID of the runtime.
            status: New status.

        Returns:
            True if status was updated, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.set_status("memory_runtime", RuntimeStatus.FAILED)
            True
        """
        return asyncio.run(self._set_status_async(runtime_id, status))

    async def _set_status_async(
        self, runtime_id: str, status: RuntimeStatus
    ) -> bool:
        """Async version of set_status."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]
            old_status = info.status

            if old_status == status:
                return False

            info.status = status

            # Update metrics
            async with self._metrics_lock:
                if old_status == RuntimeStatus.RUNNING and status != RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] -= 1
                elif old_status != RuntimeStatus.RUNNING and status == RuntimeStatus.RUNNING:
                    self._metrics["runtimes_running"] += 1
                if status == RuntimeStatus.FAILED:
                    self._metrics["runtimes_failed"] += 1
                elif old_status == RuntimeStatus.FAILED:
                    self._metrics["runtimes_failed"] -= 1

            # Call status change callbacks
            for callback in self._on_status_change:
                try:
                    callback(runtime_id, old_status, status)
                except Exception as e:
                    logger.error(f"Error in status change callback: {e}")

            if self._enable_logging:
                logger.info(f"Runtime status changed: {runtime_id} -> {status.value}")

            return True

    def update_heartbeat(self, runtime_id: str) -> bool:
        """
        Update the heartbeat for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if heartbeat was updated, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.update_heartbeat("memory_runtime")
            True
        """
        return asyncio.run(self._update_heartbeat_async(runtime_id))

    async def _update_heartbeat_async(self, runtime_id: str) -> bool:
        """Async version of update_heartbeat."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            self._runtimes[runtime_id].last_heartbeat = datetime.utcnow()
            return True

    def add_capability(
        self, runtime_id: str, capability: str
    ) -> bool:
        """
        Add a capability to a runtime.

        Args:
            runtime_id: ID of the runtime.
            capability: Capability to add.

        Returns:
            True if capability was added, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> registry.add_capability("memory_runtime", "storage")
            True
        """
        return asyncio.run(self._add_capability_async(runtime_id, capability))

    async def _add_capability_async(
        self, runtime_id: str, capability: str
    ) -> bool:
        """Async version of add_capability."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]

            if capability in info.capabilities:
                return False

            info.capabilities.add(capability)

            # Update index
            async with self._indexes_lock:
                self._by_capability[capability].add(runtime_id)

            if self._enable_logging:
                logger.info(f"Capability added: {capability} to {runtime_id}")

            return True

    def remove_capability(
        self, runtime_id: str, capability: str
    ) -> bool:
        """
        Remove a capability from a runtime.

        Args:
            runtime_id: ID of the runtime.
            capability: Capability to remove.

        Returns:
            True if capability was removed, False otherwise.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", capabilities={"storage"})
            >>> registry.remove_capability("memory_runtime", "storage")
            True
        """
        return asyncio.run(
            self._remove_capability_async(runtime_id, capability)
        )

    async def _remove_capability_async(
        self, runtime_id: str, capability: str
    ) -> bool:
        """Async version of remove_capability."""
        async with self._runtimes_lock:
            if runtime_id not in self._runtimes:
                return False

            info = self._runtimes[runtime_id]

            if capability not in info.capabilities:
                return False

            info.capabilities.remove(capability)

            # Update index
            async with self._indexes_lock:
                if capability in self._by_capability:
                    self._by_capability[capability].discard(runtime_id)

            if self._enable_logging:
                logger.info(f"Capability removed: {capability} from {runtime_id}")

            return True

    def on_register(
        self, callback: Callable[[str, RuntimeInfo], None]
    ) -> None:
        """
        Register a callback for runtime registration.

        Args:
            callback: Callback function to call when a runtime is registered.

        Example:
            >>> registry = RuntimeRegistry()
            >>> def on_register(runtime_id, info):
            ...     print(f"Runtime registered: {runtime_id}")
            >>> registry.on_register(on_register)
        """
        self._on_register.append(callback)

    def on_unregister(
        self, callback: Callable[[str, RuntimeInfo], None]
    ) -> None:
        """
        Register a callback for runtime unregistration.

        Args:
            callback: Callback function to call when a runtime is unregistered.

        Example:
            >>> registry = RuntimeRegistry()
            >>> def on_unregister(runtime_id, info):
            ...     print(f"Runtime unregistered: {runtime_id}")
            >>> registry.on_unregister(on_unregister)
        """
        self._on_unregister.append(callback)

    def on_status_change(
        self, callback: Callable[[str, RuntimeStatus, RuntimeStatus], None]
    ) -> None:
        """
        Register a callback for runtime status changes.

        Args:
            callback: Callback function to call when a runtime's status changes.

        Example:
            >>> registry = RuntimeRegistry()
            >>> def on_status_change(runtime_id, old_status, new_status):
            ...     print(f"Status changed: {runtime_id} {old_status} -> {new_status}")
            >>> registry.on_status_change(on_status_change)
        """
        self._on_status_change.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get registry metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> registry = RuntimeRegistry()
            >>> metrics = registry.get_metrics()
            >>> metrics["runtimes_registered"]
            0
        """
        return {
            **self._metrics,
            "runtimes_count": len(self._runtimes),
            "types_count": len(self._by_type),
            "capabilities_count": len(self._by_capability),
        }

    def clear(self) -> int:
        """
        Clear all registered runtimes.

        Returns:
            Number of runtimes cleared.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.register("memory_runtime", name="Memory Runtime")
            >>> count = registry.clear()
            >>> count
            1
        """
        count = len(self._runtimes)
        self._runtimes.clear()
        self._by_name.clear()
        self._by_type.clear()
        self._by_capability.clear()
        self._metrics = {
            "runtimes_registered": 0,
            "runtimes_unregistered": 0,
            "runtimes_running": 0,
            "runtimes_failed": 0,
            "registrations_rejected": 0,
        }
        return count

    def shutdown(self) -> None:
        """
        Shutdown the runtime registry.

        Cleans up resources and stops all processing.

        Example:
            >>> registry = RuntimeRegistry()
            >>> registry.shutdown()
        """
        self.clear()
        self._on_register.clear()
        self._on_unregister.clear()
        self._on_status_change.clear()

        logger.info("Runtime registry shutdown complete")

    def __repr__(self) -> str:
        """Return string representation of the runtime registry."""
        return (
            f"RuntimeRegistry("
            f"runtimes={len(self._runtimes)}, "
            f"running={self._metrics['runtimes_running']}, "
            f"failed={self._metrics['runtimes_failed']})"
        )
