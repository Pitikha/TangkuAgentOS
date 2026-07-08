"""
Runtime Communication Framework - Runtime Discovery Service

The RuntimeDiscoveryService provides service discovery capabilities for
TangkuAgentOS runtimes. It enables:
- Runtime discovery by various criteria
- Service location
- Endpoint resolution
- Capability-based discovery
- Health-aware discovery

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
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
    Tuple,
    Union,
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


class DiscoveryStrategy(Enum):
    """
    Discovery strategies for finding runtimes.

    Attributes:
        RANDOM: Select a random runtime from matching candidates.
        ROUND_ROBIN: Select runtimes in round-robin order.
        LEAST_LOADED: Select the least loaded runtime.
        MOST_AVAILABLE: Select the runtime with the most available capacity.
        HEALTHIEST: Select the healthiest runtime.
        FIRST_AVAILABLE: Select the first available runtime.
        ALL: Return all matching runtimes.
    """

    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    MOST_AVAILABLE = "most_available"
    HEALTHIEST = "healthiest"
    FIRST_AVAILABLE = "first_available"
    ALL = "all"


@dataclass
class DiscoveryCriteria:
    """
    Criteria for discovering runtimes.

    Attributes:
        capability: Required capability.
        capabilities: Required capabilities (AND).
        any_capability: Any of these capabilities (OR).
        type: Runtime type.
        types: Runtime types.
        name: Runtime name.
        names: Runtime names.
        status: Required status.
        statuses: Required statuses.
        min_version: Minimum version.
        max_version: Maximum version.
        metadata: Required metadata key-value pairs.
        custom_filter: Custom filter function.
        limit: Maximum number of results.
        strategy: Discovery strategy.
    """

    capability: Optional[str] = None
    capabilities: Optional[Set[str]] = None
    any_capability: Optional[Set[str]] = None
    type: Optional[str] = None
    types: Optional[Set[str]] = None
    name: Optional[str] = None
    names: Optional[Set[str]] = None
    status: Optional[str] = None
    statuses: Optional[Set[str]] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    custom_filter: Optional[Callable[["RuntimeInfo"], bool]] = None
    limit: int = 10
    strategy: DiscoveryStrategy = DiscoveryStrategy.FIRST_AVAILABLE


@dataclass
class DiscoveryResult:
    """
    Result of a discovery query.

    Attributes:
        runtime_id: ID of the discovered runtime.
        runtime_info: Information about the runtime.
        score: Score or priority of the result.
        endpoint: Resolved endpoint.
        health_status: Health status of the runtime.
        last_heartbeat: Last heartbeat timestamp.
    """

    runtime_id: str
    runtime_info: "RuntimeInfo"
    score: float = 1.0
    endpoint: Optional[str] = None
    health_status: Optional[str] = None
    last_heartbeat: Optional[datetime] = None


@dataclass
class ServiceEndpoint:
    """
    Represents a service endpoint for a runtime.

    Attributes:
        runtime_id: ID of the runtime.
        service_name: Name of the service.
        endpoint_url: URL of the endpoint.
        protocol: Protocol (e.g., "http", "grpc", "websocket").
        port: Port number.
        path: Path or route.
        metadata: Additional endpoint metadata.
        health_check_url: URL for health checks.
        created_at: When the endpoint was registered.
        last_checked: Last health check timestamp.
        is_healthy: Whether the endpoint is healthy.
    """

    runtime_id: str
    service_name: str
    endpoint_url: str
    protocol: str = "http"
    port: int = 0
    path: str = "/"
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    is_healthy: bool = True


class RuntimeDiscoveryService:
    """
    Service discovery for TangkuAgentOS runtimes.

    The RuntimeDiscoveryService provides capabilities for discovering
    runtimes based on various criteria including capabilities, types,
    status, and custom filters. It supports multiple discovery strategies
    and can integrate with health monitoring systems.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.discovery import RuntimeDiscoveryService
        >>> from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
        >>> 
        >>> registry = RuntimeRegistry()
        >>> discovery = RuntimeDiscoveryService(registry)
        >>> 
        >>> # Register some runtimes
        >>> registry.register("memory_runtime", type="memory", capabilities={"storage"})
        >>> registry.register("cache_runtime", type="cache", capabilities={"storage", "caching"})
        >>> 
        >>> # Discover runtimes with storage capability
        >>> results = discovery.discover(capability="storage")
        >>> len(results)
        2

    Attributes:
        registry: Runtime registry to use for discovery.
    """

    def __init__(
        self,
        registry: Optional["RuntimeRegistry"] = None,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime discovery service.

        Args:
            registry: Runtime registry to use for discovery.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        self._registry = registry
        self._owns_registry = registry is None

        if self._registry is None:
            from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry

            self._registry = RuntimeRegistry()

        # Service endpoints: (runtime_id, service_name) -> ServiceEndpoint
        self._endpoints: Dict[Tuple[str, str], ServiceEndpoint] = {}
        self._endpoints_lock = asyncio.Lock()

        # Round-robin state
        self._round_robin_index: Dict[str, int] = {}
        self._round_robin_lock = asyncio.Lock()

        # Load tracking
        self._runtime_load: Dict[str, float] = {}  # runtime_id -> load (0-1)
        self._load_lock = asyncio.Lock()

        # Metrics
        self._metrics: Dict[str, Any] = {
            "discovery_queries": 0,
            "runtimes_discovered": 0,
            "endpoints_registered": 0,
            "endpoints_resolved": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info("RuntimeDiscoveryService initialized")

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        return self._registry

    def discover(
        self,
        criteria: Optional[DiscoveryCriteria] = None,
        **kwargs,
    ) -> List[DiscoveryResult]:
        """
        Discover runtimes matching the given criteria.

        Args:
            criteria: Discovery criteria.
            **kwargs: Additional criteria as keyword arguments.

        Returns:
            List of discovery results.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> 
            >>> # Discover by capability
            >>> results = discovery.discover(capability="storage")
            >>> 
            >>> # Discover by type
            >>> results = discovery.discover(type="memory")
            >>> 
            >>> # Discover with multiple criteria
            >>> results = discovery.discover(
            ...     capability="storage",
            ...     status="running",
            ...     limit=5
            ... )
        """
        # Build criteria from kwargs if not provided
        if criteria is None:
            criteria = DiscoveryCriteria(**kwargs)

        # Update metrics
        async with self._metrics_lock:
            self._metrics["discovery_queries"] += 1

        # Get all runtimes
        all_runtimes = list(self._registry._runtimes.values())

        # Filter runtimes
        filtered = self._filter_runtimes(all_runtimes, criteria)

        # Sort and select based on strategy
        results = self._select_results(filtered, criteria)

        # Update metrics
        async with self._metrics_lock:
            self._metrics["runtimes_discovered"] += len(results)

        return results

    def discover_one(
        self,
        criteria: Optional[DiscoveryCriteria] = None,
        **kwargs,
    ) -> Optional[DiscoveryResult]:
        """
        Discover a single runtime matching the given criteria.

        Args:
            criteria: Discovery criteria.
            **kwargs: Additional criteria as keyword arguments.

        Returns:
            Single discovery result or None if no match.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> result = discovery.discover_one(capability="storage")
        """
        criteria = DiscoveryCriteria(**kwargs) if criteria is None else criteria
        criteria.limit = 1
        criteria.strategy = DiscoveryStrategy.FIRST_AVAILABLE

        results = self.discover(criteria)
        return results[0] if results else None

    def discover_by_capability(
        self,
        capability: str,
        strategy: DiscoveryStrategy = DiscoveryStrategy.FIRST_AVAILABLE,
        limit: int = 10,
    ) -> List[DiscoveryResult]:
        """
        Discover runtimes with a specific capability.

        Args:
            capability: Required capability.
            strategy: Discovery strategy.
            limit: Maximum number of results.

        Returns:
            List of discovery results.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> results = discovery.discover_by_capability("storage")
        """
        criteria = DiscoveryCriteria(
            capability=capability,
            strategy=strategy,
            limit=limit,
        )
        return self.discover(criteria)

    def discover_by_type(
        self,
        type: str,
        strategy: DiscoveryStrategy = DiscoveryStrategy.FIRST_AVAILABLE,
        limit: int = 10,
    ) -> List[DiscoveryResult]:
        """
        Discover runtimes of a specific type.

        Args:
            type: Runtime type.
            strategy: Discovery strategy.
            limit: Maximum number of results.

        Returns:
            List of discovery results.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> results = discovery.discover_by_type("memory")
        """
        criteria = DiscoveryCriteria(
            type=type,
            strategy=strategy,
            limit=limit,
        )
        return self.discover(criteria)

    def discover_by_status(
        self,
        status: Union[str, "RuntimeStatus"],
        strategy: DiscoveryStrategy = DiscoveryStrategy.FIRST_AVAILABLE,
        limit: int = 10,
    ) -> List[DiscoveryResult]:
        """
        Discover runtimes with a specific status.

        Args:
            status: Required status.
            strategy: Discovery strategy.
            limit: Maximum number of results.

        Returns:
            List of discovery results.

        Example:
            >>> from tangku_agentos.runtime_communication.services.registry import RuntimeStatus
            >>> discovery = RuntimeDiscoveryService()
            >>> results = discovery.discover_by_status(RuntimeStatus.RUNNING)
        """
        from tangku_agentos.runtime_communication.services.registry import RuntimeStatus

        if isinstance(status, str):
            status = RuntimeStatus(status)

        criteria = DiscoveryCriteria(
            status=status.value,
            strategy=strategy,
            limit=limit,
        )
        return self.discover(criteria)

    def get_endpoint(
        self,
        runtime_id: str,
        service_name: str = "default",
    ) -> Optional[str]:
        """
        Get the endpoint for a runtime service.

        Args:
            runtime_id: ID of the runtime.
            service_name: Name of the service (default: "default").

        Returns:
            Endpoint URL or None if not found.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> endpoint = discovery.get_endpoint("memory_runtime")
        """
        async with self._endpoints_lock:
            endpoint = self._endpoints.get((runtime_id, service_name))
            if endpoint:
                async with self._metrics_lock:
                    self._metrics["endpoints_resolved"] += 1
                return endpoint.endpoint_url

        # Fall back to runtime's endpoint
        runtime_info = self._registry.get(runtime_id)
        if runtime_info and runtime_info.endpoint:
            return runtime_info.endpoint

        return None

    def register_endpoint(
        self,
        runtime_id: str,
        service_name: str,
        endpoint_url: str,
        protocol: str = "http",
        port: int = 0,
        path: str = "/",
        metadata: Optional[Dict[str, Any]] = None,
        health_check_url: Optional[str] = None,
    ) -> None:
        """
        Register a service endpoint for a runtime.

        Args:
            runtime_id: ID of the runtime.
            service_name: Name of the service.
            endpoint_url: URL of the endpoint.
            protocol: Protocol (e.g., "http", "grpc", "websocket").
            port: Port number.
            path: Path or route.
            metadata: Additional endpoint metadata.
            health_check_url: URL for health checks.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> discovery.register_endpoint(
            ...     "memory_runtime",
            ...     "storage",
            ...     "http://localhost:8080/storage"
            ... )
        """
        endpoint = ServiceEndpoint(
            runtime_id=runtime_id,
            service_name=service_name,
            endpoint_url=endpoint_url,
            protocol=protocol,
            port=port,
            path=path,
            metadata=metadata or {},
            health_check_url=health_check_url,
        )

        asyncio.run(self._register_endpoint_async(endpoint))

    async def _register_endpoint_async(self, endpoint: ServiceEndpoint) -> None:
        """Async version of register_endpoint."""
        async with self._endpoints_lock:
            self._endpoints[(endpoint.runtime_id, endpoint.service_name)] = endpoint

            async with self._metrics_lock:
                self._metrics["endpoints_registered"] += 1

            if self._enable_logging:
                logger.info(
                    f"Endpoint registered: {endpoint.service_name} "
                    f"for {endpoint.runtime_id} at {endpoint.endpoint_url}"
                )

    def unregister_endpoint(
        self, runtime_id: str, service_name: str = "default"
    ) -> bool:
        """
        Unregister a service endpoint.

        Args:
            runtime_id: ID of the runtime.
            service_name: Name of the service.

        Returns:
            True if endpoint was unregistered, False otherwise.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> discovery.register_endpoint("memory_runtime", "storage", "http://...")
            >>> discovery.unregister_endpoint("memory_runtime", "storage")
            True
        """
        return asyncio.run(
            self._unregister_endpoint_async(runtime_id, service_name)
        )

    async def _unregister_endpoint_async(
        self, runtime_id: str, service_name: str = "default"
    ) -> bool:
        """Async version of unregister_endpoint."""
        async with self._endpoints_lock:
            key = (runtime_id, service_name)
            if key in self._endpoints:
                del self._endpoints[key]

                async with self._metrics_lock:
                    self._metrics["endpoints_registered"] -= 1

                if self._enable_logging:
                    logger.info(
                        f"Endpoint unregistered: {service_name} for {runtime_id}"
                    )
                return True
            return False

    def update_load(
        self, runtime_id: str, load: float
    ) -> None:
        """
        Update the load for a runtime.

        Args:
            runtime_id: ID of the runtime.
            load: Load value (0-1).

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> discovery.update_load("memory_runtime", 0.5)
        """
        asyncio.run(self._update_load_async(runtime_id, load))

    async def _update_load_async(self, runtime_id: str, load: float) -> None:
        """Async version of update_load."""
        # Clamp load to 0-1 range
        load = max(0.0, min(1.0, load))

        async with self._load_lock:
            self._runtime_load[runtime_id] = load

        if self._enable_logging:
            logger.debug(f"Load updated: {runtime_id} = {load}")

    def get_load(self, runtime_id: str) -> float:
        """
        Get the load for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Load value (0-1), defaults to 0.0 if not found.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> load = discovery.get_load("memory_runtime")
        """
        return self._runtime_load.get(runtime_id, 0.0)

    def list_endpoints(self, runtime_id: Optional[str] = None) -> List[ServiceEndpoint]:
        """
        List all registered endpoints.

        Args:
            runtime_id: Filter by runtime ID (optional).

        Returns:
            List of service endpoints.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> endpoints = discovery.list_endpoints()
        """
        if runtime_id is not None:
            return [
                ep
                for key, ep in self._endpoints.items()
                if key[0] == runtime_id
            ]
        return list(self._endpoints.values())

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get discovery service metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> metrics = discovery.get_metrics()
            >>> metrics["discovery_queries"]
            0
        """
        return {
            **self._metrics,
            "endpoints_count": len(self._endpoints),
            "load_tracked": len(self._runtime_load),
        }

    def clear(self) -> None:
        """
        Clear all discovery data.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> discovery.clear()
        """
        self._endpoints.clear()
        self._round_robin_index.clear()
        self._runtime_load.clear()
        self._metrics = {
            "discovery_queries": 0,
            "runtimes_discovered": 0,
            "endpoints_registered": 0,
            "endpoints_resolved": 0,
        }

    def shutdown(self) -> None:
        """
        Shutdown the discovery service.

        Example:
            >>> discovery = RuntimeDiscoveryService()
            >>> discovery.shutdown()
        """
        self.clear()

        if self._owns_registry:
            self._registry.shutdown()

        logger.info("Runtime discovery service shutdown complete")

    def _filter_runtimes(
        self,
        runtimes: List["RuntimeInfo"],
        criteria: DiscoveryCriteria,
    ) -> List["RuntimeInfo"]:
        """
        Filter runtimes based on criteria.

        Args:
            runtimes: List of runtimes to filter.
            criteria: Discovery criteria.

        Returns:
            Filtered list of runtimes.
        """
        from tangku_agentos.runtime_communication.services.registry import RuntimeStatus

        filtered = []

        for runtime in runtimes:
            # Check capability
            if criteria.capability is not None:
                if not runtime.has_capability(criteria.capability):
                    continue

            # Check capabilities (AND)
            if criteria.capabilities is not None:
                if not all(
                    runtime.has_capability(cap) for cap in criteria.capabilities
                ):
                    continue

            # Check any capability (OR)
            if criteria.any_capability is not None:
                if not any(
                    runtime.has_capability(cap) for cap in criteria.any_capability
                ):
                    continue

            # Check type
            if criteria.type is not None:
                if runtime.type != criteria.type:
                    continue

            # Check types
            if criteria.types is not None:
                if runtime.type not in criteria.types:
                    continue

            # Check name
            if criteria.name is not None:
                if runtime.name != criteria.name:
                    continue

            # Check names
            if criteria.names is not None:
                if runtime.name not in criteria.names:
                    continue

            # Check status
            if criteria.status is not None:
                if runtime.status.value != criteria.status:
                    continue

            # Check statuses
            if criteria.statuses is not None:
                if runtime.status.value not in criteria.statuses:
                    continue

            # Check version
            if criteria.min_version is not None:
                if runtime.version < criteria.min_version:
                    continue

            if criteria.max_version is not None:
                if runtime.version > criteria.max_version:
                    continue

            # Check metadata
            if criteria.metadata is not None:
                for key, value in criteria.metadata.items():
                    if runtime.metadata.get(key) != value:
                        continue

            # Check custom filter
            if criteria.custom_filter is not None:
                try:
                    if not criteria.custom_filter(runtime):
                        continue
                except Exception as e:
                    logger.error(f"Error in custom filter: {e}")
                    continue

            filtered.append(runtime)

        return filtered

    def _select_results(
        self,
        runtimes: List["RuntimeInfo"],
        criteria: DiscoveryCriteria,
    ) -> List[DiscoveryResult]:
        """
        Select results based on discovery strategy.

        Args:
            runtimes: Filtered list of runtimes.
            criteria: Discovery criteria.

        Returns:
            List of discovery results.
        """
        if not runtimes:
            return []

        # Apply limit
        if criteria.limit > 0 and len(runtimes) > criteria.limit:
            if criteria.strategy == DiscoveryStrategy.RANDOM:
                import random

                runtimes = random.sample(runtimes, criteria.limit)
            else:
                runtimes = runtimes[: criteria.limit]

        # Convert to discovery results
        results = []
        for runtime in runtimes:
            result = DiscoveryResult(
                runtime_id=runtime.runtime_id,
                runtime_info=runtime,
                endpoint=self.get_endpoint(runtime.runtime_id),
                health_status=runtime.status.value,
                last_heartbeat=runtime.last_heartbeat,
            )
            results.append(result)

        # Apply strategy-specific sorting
        if criteria.strategy == DiscoveryStrategy.LEAST_LOADED:
            results.sort(
                key=lambda r: self.get_load(r.runtime_id),
                reverse=False,
            )
        elif criteria.strategy == DiscoveryStrategy.MOST_AVAILABLE:
            results.sort(
                key=lambda r: 1.0 - self.get_load(r.runtime_id),
                reverse=True,
            )
        elif criteria.strategy == DiscoveryStrategy.HEALTHIEST:
            # Sort by health status (running > degraded > others)
            status_order = {
                "running": 0,
                "degraded": 1,
                "starting": 2,
                "paused": 3,
                "stopping": 4,
                "stopped": 5,
                "failed": 6,
                "unresponsive": 7,
                "registered": 8,
            }
            results.sort(
                key=lambda r: status_order.get(r.health_status, 9),
                reverse=False,
            )
        elif criteria.strategy == DiscoveryStrategy.ROUND_ROBIN:
            async with self._round_robin_lock:
                key = criteria.capability or criteria.type or "default"
                if key not in self._round_robin_index:
                    self._round_robin_index[key] = 0

                # Sort by index
                index = self._round_robin_index[key]
                results = results[index:] + results[:index]

                # Update index for next time
                self._round_robin_index[key] = (
                    self._round_robin_index[key] + 1
                ) % len(results)

        # For FIRST_AVAILABLE and ALL, keep the original order
        # For RANDOM, we already shuffled

        # Apply limit again in case we added more
        if criteria.limit > 0:
            results = results[: criteria.limit]

        return results

    def __repr__(self) -> str:
        """Return string representation of the discovery service."""
        return (
            f"RuntimeDiscoveryService("
            f"runtimes={len(self._registry._runtimes)}, "
            f"endpoints={len(self._endpoints)}, "
            f"load_tracked={len(self._runtime_load)})"
        )
