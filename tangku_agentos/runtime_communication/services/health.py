"""
Runtime Communication Framework - Runtime Health Service

The RuntimeHealthService provides health monitoring capabilities for
TangkuAgentOS runtimes. It enables:
- Health status tracking
- Health check execution
- Health metric collection
- Health-based discovery
- Health alerting

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    from tangku_agentos.runtime_communication.services.registry import (
        RuntimeRegistry,
        RuntimeInfo,
        RuntimeStatus,
    )

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """
    Health status levels for runtimes.

    Attributes:
        HEALTHY: Runtime is healthy and operating normally.
        DEGRADED: Runtime is operating but with issues.
        UNHEALTHY: Runtime is not healthy and may not be functioning properly.
        UNKNOWN: Health status is unknown (e.g., no health checks performed yet).
        STARTING: Runtime is starting up.
        STOPPING: Runtime is stopping.
        STOPPED: Runtime has stopped.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class HealthCheckResult:
    """
    Result of a health check.

    Attributes:
        runtime_id: ID of the runtime.
        check_name: Name of the health check.
        status: Health status.
        message: Status message.
        details: Additional details.
        timestamp: When the check was performed.
        duration_ms: Duration of the check in milliseconds.
        passed: Whether the check passed.
    """

    runtime_id: str
    check_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "check_name": self.check_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "passed": self.passed,
        }


@dataclass
class HealthCheck:
    """
    Definition of a health check.

    Attributes:
        name: Name of the health check.
        description: Description of the health check.
        check_func: Function to perform the health check.
        interval: Interval between checks in seconds.
        timeout: Timeout for the check in seconds.
        enabled: Whether the check is enabled.
        critical: Whether this is a critical check (failure makes runtime unhealthy).
    """

    name: str
    description: str = ""
    check_func: Callable[[str], HealthCheckResult]
    interval: float = 30.0
    timeout: float = 10.0
    enabled: bool = True
    critical: bool = True


@dataclass
class RuntimeHealth:
    """
    Health information for a runtime.

    Attributes:
        runtime_id: ID of the runtime.
        status: Overall health status.
        last_checked: Last health check timestamp.
        last_status_change: Last time the status changed.
        checks: Results of individual health checks.
        metrics: Health metrics.
        uptime: Runtime uptime in seconds.
        consecutive_failures: Number of consecutive health check failures.
    """

    runtime_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_checked: Optional[datetime] = None
    last_status_change: Optional[datetime] = None
    checks: Dict[str, HealthCheckResult] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    uptime: float = 0.0
    consecutive_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "status": self.status.value,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_status_change": self.last_status_change.isoformat()
            if self.last_status_change
            else None,
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
            "metrics": self.metrics,
            "uptime": self.uptime,
            "consecutive_failures": self.consecutive_failures,
        }


@dataclass
class HealthAlert:
    """
    Health alert for a runtime.

    Attributes:
        alert_id: Unique identifier for the alert.
        runtime_id: ID of the runtime.
        status: Health status that triggered the alert.
        message: Alert message.
        severity: Alert severity (info, warning, error, critical).
        timestamp: When the alert was created.
        resolved: Whether the alert has been resolved.
        resolved_at: When the alert was resolved.
        metadata: Additional alert metadata.
    """

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    runtime_id: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    severity: str = "info"  # info, warning, error, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve(self) -> None:
        """Mark the alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "runtime_id": self.runtime_id,
            "status": self.status.value,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }


class RuntimeHealthService:
    """
    Health monitoring service for TangkuAgentOS runtimes.

    The RuntimeHealthService provides comprehensive health monitoring for
    runtimes including:
    - Health status tracking
    - Health check execution
    - Health metric collection
    - Health-based discovery
    - Health alerting

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.health import RuntimeHealthService
        >>> from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
        >>> 
        >>> registry = RuntimeRegistry()
        >>> health = RuntimeHealthService(registry)
        >>> 
        >>> # Register a runtime
        >>> registry.register("memory_runtime", name="Memory Runtime")
        >>> 
        >>> # Check health
        >>> status = health.get_health("memory_runtime")
        >>> status.status
        HealthStatus.UNKNOWN

    Attributes:
        registry: Runtime registry to monitor.
        check_interval: Default interval between health checks in seconds.
        check_timeout: Default timeout for health checks in seconds.
    """

    def __init__(
        self,
        registry: Optional["RuntimeRegistry"] = None,
        check_interval: float = 30.0,
        check_timeout: float = 10.0,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime health service.

        Args:
            registry: Runtime registry to monitor.
            check_interval: Default interval between health checks in seconds.
            check_timeout: Default timeout for health checks in seconds.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        self._registry = registry
        self._owns_registry = registry is None

        if self._registry is None:
            from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry

            self._registry = RuntimeRegistry()

        # Health information: runtime_id -> RuntimeHealth
        self._health: Dict[str, RuntimeHealth] = {}
        self._health_lock = asyncio.Lock()

        # Health checks: runtime_id -> List[HealthCheck]
        self._checks: Dict[str, List[HealthCheck]] = {}
        self._checks_lock = asyncio.Lock()

        # Health alerts: alert_id -> HealthAlert
        self._alerts: Dict[str, HealthAlert] = {}
        self._alerts_lock = asyncio.Lock()

        # Configuration
        self._check_interval = check_interval
        self._check_timeout = check_timeout

        # Alert callbacks
        self._on_alert: List[Callable[[HealthAlert], None]] = []
        self._on_resolve: List[Callable[[HealthAlert], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "health_checks_performed": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "alerts_triggered": 0,
            "alerts_resolved": 0,
            "runtimes_healthy": 0,
            "runtimes_degraded": 0,
            "runtimes_unhealthy": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        # Background monitoring
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info(
            f"RuntimeHealthService initialized with interval={check_interval}, "
            f"timeout={check_timeout}"
        )

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        return self._registry

    async def start(self) -> None:
        """
        Start the health monitoring service.

        This starts the background task that performs periodic health checks.

        Example:
            >>> health = RuntimeHealthService()
            >>> asyncio.run(health.start())
        """
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_health())

        if self._enable_logging:
            logger.info("Runtime health service started")

    async def stop(self) -> None:
        """
        Stop the health monitoring service.

        This stops the background monitoring task.

        Example:
            >>> health = RuntimeHealthService()
            >>> asyncio.run(health.start())
            >>> asyncio.run(health.stop())
        """
        if not self._running:
            return

        self._running = False

        if self._monitor_task is not None:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._enable_logging:
            logger.info("Runtime health service stopped")

    def get_health(self, runtime_id: str) -> Optional[RuntimeHealth]:
        """
        Get the health information for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            RuntimeHealth if found, None otherwise.

        Example:
            >>> health = RuntimeHealthService()
            >>> health_info = health.get_health("memory_runtime")
        """
        return self._health.get(runtime_id)

    def get_status(self, runtime_id: str) -> HealthStatus:
        """
        Get the health status for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            HealthStatus for the runtime.

        Example:
            >>> health = RuntimeHealthService()
            >>> status = health.get_status("memory_runtime")
        """
        health_info = self.get_health(runtime_id)
        if health_info:
            return health_info.status
        return HealthStatus.UNKNOWN

    def is_healthy(self, runtime_id: str) -> bool:
        """
        Check if a runtime is healthy.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if runtime is healthy, False otherwise.

        Example:
            >>> health = RuntimeHealthService()
            >>> health.is_healthy("memory_runtime")
            False
        """
        status = self.get_status(runtime_id)
        return status == HealthStatus.HEALTHY

    def is_available(self, runtime_id: str) -> bool:
        """
        Check if a runtime is available (healthy or degraded).

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if runtime is available, False otherwise.

        Example:
            >>> health = RuntimeHealthService()
            >>> health.is_available("memory_runtime")
            False
        """
        status = self.get_status(runtime_id)
        return status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    async def check_health(self, runtime_id: str) -> Optional[RuntimeHealth]:
        """
        Perform a health check for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            RuntimeHealth with updated health information.

        Example:
            >>> health = RuntimeHealthService()
            >>> health_info = asyncio.run(health.check_health("memory_runtime"))
        """
        # Get runtime info
        runtime_info = self._registry.get(runtime_id)
        if runtime_info is None:
            return None

        # Initialize health info if not exists
        if runtime_id not in self._health:
            self._health[runtime_id] = RuntimeHealth(
                runtime_id=runtime_id,
            )

        health_info = self._health[runtime_id]
        old_status = health_info.status

        # Perform all registered health checks
        async with self._checks_lock:
            checks = list(self._checks.get(runtime_id, []))

        for check in checks:
            if not check.enabled:
                continue

            try:
                # Perform the check
                start_time = datetime.utcnow()
                result = await asyncio.wait_for(
                    asyncio.to_thread(check.check_func, runtime_id),
                    timeout=check.timeout,
                )
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                result.duration_ms = duration_ms

                # Store result
                health_info.checks[check.name] = result

                # Update metrics
                async with self._metrics_lock:
                    self._metrics["health_checks_performed"] += 1
                    if result.passed:
                        self._metrics["health_checks_passed"] += 1
                    else:
                        self._metrics["health_checks_failed"] += 1

            except asyncio.TimeoutError:
                result = HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {check.timeout}s",
                    passed=False,
                )
                health_info.checks[check.name] = result

                async with self._metrics_lock:
                    self._metrics["health_checks_performed"] += 1
                    self._metrics["health_checks_failed"] += 1

            except Exception as e:
                result = HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    passed=False,
                )
                health_info.checks[check.name] = result

                async with self._metrics_lock:
                    self._metrics["health_checks_performed"] += 1
                    self._metrics["health_checks_failed"] += 1

        # Determine overall status
        new_status = self._determine_status(health_info, runtime_info)

        # Update health info
        health_info.status = new_status
        health_info.last_checked = datetime.utcnow()

        # Update consecutive failures
        if new_status != HealthStatus.HEALTHY:
            health_info.consecutive_failures += 1
        else:
            health_info.consecutive_failures = 0

        # Update status change timestamp
        if new_status != old_status:
            health_info.last_status_change = datetime.utcnow()

            # Update metrics
            async with self._metrics_lock:
                if old_status == HealthStatus.HEALTHY:
                    self._metrics["runtimes_healthy"] -= 1
                elif old_status == HealthStatus.DEGRADED:
                    self._metrics["runtimes_degraded"] -= 1
                elif old_status == HealthStatus.UNHEALTHY:
                    self._metrics["runtimes_unhealthy"] -= 1

                if new_status == HealthStatus.HEALTHY:
                    self._metrics["runtimes_healthy"] += 1
                elif new_status == HealthStatus.DEGRADED:
                    self._metrics["runtimes_degraded"] += 1
                elif new_status == HealthStatus.UNHEALTHY:
                    self._metrics["runtimes_unhealthy"] += 1

            # Trigger alerts if needed
            if new_status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY):
                await self._trigger_alert(runtime_id, new_status)
            elif old_status in (HealthStatus.DEGRADED, HealthStatus.UNHEALTHY):
                await self._resolve_alerts(runtime_id)

        return health_info

    def register_check(
        self,
        runtime_id: str,
        check: HealthCheck,
    ) -> None:
        """
        Register a health check for a runtime.

        Args:
            runtime_id: ID of the runtime.
            check: Health check to register.

        Example:
            >>> health = RuntimeHealthService()
            >>> 
            >>> def check_memory_usage(runtime_id: str) -> HealthCheckResult:
            ...     # Check memory usage
            ...     return HealthCheckResult(
            ...         runtime_id=runtime_id,
            ...         check_name="memory_usage",
            ...         status=HealthStatus.HEALTHY,
            ...         passed=True
            ...     )
            >>> 
            >>> check = HealthCheck(
            ...     name="memory_usage",
            ...     description="Check memory usage",
            ...     check_func=check_memory_usage,
            ...     interval=60.0
            ... )
            >>> health.register_check("memory_runtime", check)
        """
        asyncio.run(self._register_check_async(runtime_id, check))

    async def _register_check_async(
        self, runtime_id: str, check: HealthCheck
    ) -> None:
        """Async version of register_check."""
        async with self._checks_lock:
            if runtime_id not in self._checks:
                self._checks[runtime_id] = []

            # Check if check with same name already exists
            for existing in self._checks[runtime_id]:
                if existing.name == check.name:
                    if self._enable_logging:
                        logger.warning(
                            f"Health check '{check.name}' already registered "
                            f"for runtime {runtime_id}"
                        )
                    return

            self._checks[runtime_id].append(check)

            if self._enable_logging:
                logger.info(
                    f"Health check registered: {check.name} for {runtime_id}"
                )

    def unregister_check(
        self, runtime_id: str, check_name: str
    ) -> bool:
        """
        Unregister a health check.

        Args:
            runtime_id: ID of the runtime.
            check_name: Name of the health check.

        Returns:
            True if check was unregistered, False otherwise.

        Example:
            >>> health = RuntimeHealthService()
            >>> # Assume check is registered
            >>> health.unregister_check("memory_runtime", "memory_usage")
            True
        """
        return asyncio.run(
            self._unregister_check_async(runtime_id, check_name)
        )

    async def _unregister_check_async(
        self, runtime_id: str, check_name: str
    ) -> bool:
        """Async version of unregister_check."""
        async with self._checks_lock:
            if runtime_id not in self._checks:
                return False

            for i, check in enumerate(self._checks[runtime_id]):
                if check.name == check_name:
                    self._checks[runtime_id].pop(i)

                    if self._enable_logging:
                        logger.info(
                            f"Health check unregistered: {check_name} from {runtime_id}"
                        )

                    # Remove from health info if exists
                    if runtime_id in self._health:
                        health_info = self._health[runtime_id]
                        if check_name in health_info.checks:
                            del health_info.checks[check_name]

                    return True

            return False

    def list_checks(self, runtime_id: str) -> List[HealthCheck]:
        """
        List all health checks for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            List of health checks.

        Example:
            >>> health = RuntimeHealthService()
            >>> checks = health.list_checks("memory_runtime")
        """
        return self._checks.get(runtime_id, [])

    def get_alerts(
        self,
        runtime_id: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[HealthAlert]:
        """
        Get health alerts.

        Args:
            runtime_id: Filter by runtime ID (optional).
            resolved: Filter by resolved status (optional).

        Returns:
            List of health alerts.

        Example:
            >>> health = RuntimeHealthService()
            >>> alerts = health.get_alerts()
        """
        if runtime_id is not None and resolved is not None:
            return [
                alert
                for alert in self._alerts.values()
                if alert.runtime_id == runtime_id and alert.resolved == resolved
            ]
        elif runtime_id is not None:
            return [
                alert
                for alert in self._alerts.values()
                if alert.runtime_id == runtime_id
            ]
        elif resolved is not None:
            return [
                alert
                for alert in self._alerts.values()
                if alert.resolved == resolved
            ]
        else:
            return list(self._alerts.values())

    def get_active_alerts(self) -> List[HealthAlert]:
        """
        Get all active (unresolved) health alerts.

        Returns:
            List of active health alerts.

        Example:
            >>> health = RuntimeHealthService()
            >>> alerts = health.get_active_alerts()
        """
        return self.get_alerts(resolved=False)

    def on_alert(
        self, callback: Callable[[HealthAlert], None]
    ) -> None:
        """
        Register a callback for health alerts.

        Args:
            callback: Callback function to call when an alert is triggered.

        Example:
            >>> health = RuntimeHealthService()
            >>> def on_alert(alert):
            ...     print(f"Alert: {alert.message}")
            >>> health.on_alert(on_alert)
        """
        self._on_alert.append(callback)

    def on_resolve(
        self, callback: Callable[[HealthAlert], None]
    ) -> None:
        """
        Register a callback for alert resolution.

        Args:
            callback: Callback function to call when an alert is resolved.

        Example:
            >>> health = RuntimeHealthService()
            >>> def on_resolve(alert):
            ...     print(f"Resolved: {alert.message}")
            >>> health.on_resolve(on_resolve)
        """
        self._on_resolve.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get health service metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> health = RuntimeHealthService()
            >>> metrics = health.get_metrics()
            >>> metrics["health_checks_performed"]
            0
        """
        return {
            **self._metrics,
            "runtimes_monitored": len(self._health),
            "checks_registered": sum(
                len(checks) for checks in self._checks.values()
            ),
            "alerts_active": len(self.get_active_alerts()),
            "alerts_total": len(self._alerts),
        }

    def clear(self) -> None:
        """
        Clear all health data.

        Example:
            >>> health = RuntimeHealthService()
            >>> health.clear()
        """
        self._health.clear()
        self._checks.clear()
        self._alerts.clear()
        self._metrics = {
            "health_checks_performed": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "alerts_triggered": 0,
            "alerts_resolved": 0,
            "runtimes_healthy": 0,
            "runtimes_degraded": 0,
            "runtimes_unhealthy": 0,
        }

    def shutdown(self) -> None:
        """
        Shutdown the health service.

        Example:
            >>> health = RuntimeHealthService()
            >>> health.shutdown()
        """
        asyncio.run(self._stop())
        self.clear()
        self._on_alert.clear()
        self._on_resolve.clear()

        if self._owns_registry:
            self._registry.shutdown()

        logger.info("Runtime health service shutdown complete")

    async def _monitor_health(self) -> None:
        """
        Monitor health of all runtimes.

        This is the background task that performs periodic health checks.
        """
        while self._running:
            try:
                # Get all registered runtimes
                runtime_ids = list(self._registry._runtimes.keys())

                # Perform health checks for each runtime
                tasks = []
                for runtime_id in runtime_ids:
                    tasks.append(self.check_health(runtime_id))

                await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for next interval
                await asyncio.sleep(self._check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self._check_interval)

    def _determine_status(
        self,
        health_info: RuntimeHealth,
        runtime_info: "RuntimeInfo",
    ) -> HealthStatus:
        """
        Determine overall health status based on check results.

        Args:
            health_info: Health information.
            runtime_info: Runtime information.

        Returns:
            Overall health status.
        """
        # If runtime is not running, map runtime status to health status
        if runtime_info.status != RuntimeStatus.RUNNING:
            status_map = {
                RuntimeStatus.RUNNING: HealthStatus.HEALTHY,
                RuntimeStatus.STARTING: HealthStatus.STARTING,
                RuntimeStatus.STOPPING: HealthStatus.STOPPING,
                RuntimeStatus.STOPPED: HealthStatus.STOPPED,
                RuntimeStatus.FAILED: HealthStatus.UNHEALTHY,
                RuntimeStatus.UNRESPONSIVE: HealthStatus.UNHEALTHY,
                RuntimeStatus.DEGRADED: HealthStatus.DEGRADED,
                RuntimeStatus.REGISTERED: HealthStatus.UNKNOWN,
                RuntimeStatus.PAUSED: HealthStatus.DEGRADED,
            }
            return status_map.get(runtime_info.status, HealthStatus.UNKNOWN)

        # If no checks, consider it healthy
        if not health_info.checks:
            return HealthStatus.HEALTHY

        # Count passed and failed checks
        passed = sum(1 for c in health_info.checks.values() if c.passed)
        failed = sum(1 for c in health_info.checks.values() if not c.passed)
        total = len(health_info.checks)

        # Count critical failures
        critical_failures = sum(
            1
            for name, check in self._checks.get(health_info.runtime_id, [])
            for result in [health_info.checks.get(name)]
            if result and not result.passed and check.critical
        )

        # Determine status
        if critical_failures > 0:
            return HealthStatus.UNHEALTHY
        elif failed > 0:
            return HealthStatus.DEGRADED
        elif passed == total:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    async def _trigger_alert(
        self, runtime_id: str, status: HealthStatus
    ) -> None:
        """
        Trigger a health alert.

        Args:
            runtime_id: ID of the runtime.
            status: Health status that triggered the alert.
        """
        # Check if there's already an active alert for this runtime and status
        for alert in self._alerts.values():
            if (
                alert.runtime_id == runtime_id
                and alert.status == status
                and not alert.resolved
            ):
                return

        # Create alert
        alert = HealthAlert(
            runtime_id=runtime_id,
            status=status,
            message=f"Runtime {runtime_id} is {status.value}",
            severity="warning" if status == HealthStatus.DEGRADED else "error",
        )

        async with self._alerts_lock:
            self._alerts[alert.alert_id] = alert

            async with self._metrics_lock:
                self._metrics["alerts_triggered"] += 1

        # Call alert callbacks
        for callback in self._on_alert:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        if self._enable_logging:
            logger.warning(f"Health alert: {alert.message}")

    async def _resolve_alerts(self, runtime_id: str) -> None:
        """
        Resolve health alerts for a runtime.

        Args:
            runtime_id: ID of the runtime.
        """
        resolved_alerts = []

        async with self._alerts_lock:
            for alert_id, alert in list(self._alerts.items()):
                if alert.runtime_id == runtime_id and not alert.resolved:
                    alert.resolve()
                    resolved_alerts.append(alert)

                    async with self._metrics_lock:
                        self._metrics["alerts_resolved"] += 1

        # Call resolve callbacks
        for alert in resolved_alerts:
            for callback in self._on_resolve:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in resolve callback: {e}")

        if self._enable_logging and resolved_alerts:
            logger.info(
                f"Health alerts resolved for {runtime_id}: "
                f"{len(resolved_alerts)} alerts"
            )

    def __repr__(self) -> str:
        """Return string representation of the health service."""
        return (
            f"RuntimeHealthService("
            f"monitored={len(self._health)}, "
            f"checks={sum(len(c) for c in self._checks.values())}, "
            f"alerts={len(self._alerts)}, "
            f"running={self._running})"
        )
