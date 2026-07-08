"""Health monitoring for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock, Thread
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import HealthCheckConfig, HealthMetrics, ProviderID

from .constants import HealthCheckStatus
from .exceptions import HealthCheckError, ProviderUnhealthyError
from .interfaces import ProviderHealth


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    provider_id: ProviderID
    status: HealthCheckStatus
    latency_ms: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProviderHealthStatus:
    """Health status for a provider."""

    provider_id: ProviderID
    status: HealthCheckStatus
    latency_ms: float
    error_rate: float
    availability: float
    last_check_time: float
    consecutive_failures: int = 0
    disabled: bool = False


class ProviderHealthMonitor(ProviderHealth):
    """
    Monitors the health of providers with:
    - Health checks
    - Latency monitoring
    - Error tracking
    - Availability monitoring
    - Rate-limit detection
    - Automatic provider disabling
    - Recovery
    """

    def __init__(self, config: Optional[HealthCheckConfig] = None) -> None:
        self._config = config or HealthCheckConfig()
        self._lock = RLock()
        self._status: Dict[ProviderID, ProviderHealthStatus] = {}
        self._check_handlers: Dict[ProviderID, Callable[[], HealthCheckResult]] = {}
        self._monitoring_threads: Dict[ProviderID, Thread] = {}
        self._running = True

    def check(self, provider_id: ProviderID) -> Dict[str, Any]:
        """Perform a health check for a provider."""
        handler = self._check_handlers.get(provider_id)
        if handler is None:
            return {
                "provider_id": provider_id,
                "status": HealthCheckStatus.UNKNOWN.value,
                "latency_ms": 0.0,
                "error": "No health check handler registered",
            }

        try:
            result = handler()
            with self._lock:
                if result.status == HealthCheckStatus.HEALTHY:
                    self._status[provider_id] = ProviderHealthStatus(
                        provider_id=provider_id,
                        status=result.status,
                        latency_ms=result.latency_ms,
                        error_rate=0.0,
                        availability=1.0,
                        last_check_time=result.timestamp,
                        consecutive_failures=0,
                        disabled=False,
                    )
                else:
                    current = self._status.get(provider_id)
                    consecutive_failures = (current.consecutive_failures + 1) if current else 1
                    if consecutive_failures >= self._config.max_failures:
                        self._status[provider_id] = ProviderHealthStatus(
                            provider_id=provider_id,
                            status=result.status,
                            latency_ms=result.latency_ms,
                            error_rate=1.0,
                            availability=0.0,
                            last_check_time=result.timestamp,
                            consecutive_failures=consecutive_failures,
                            disabled=True,
                        )
                    else:
                        self._status[provider_id] = ProviderHealthStatus(
                            provider_id=provider_id,
                            status=result.status,
                            latency_ms=result.latency_ms,
                            error_rate=0.5,
                            availability=0.5,
                            last_check_time=result.timestamp,
                            consecutive_failures=consecutive_failures,
                            disabled=False,
                        )
            return {
                "provider_id": provider_id,
                "status": result.status.value,
                "latency_ms": result.latency_ms,
                "error": result.error,
            }
        except Exception as e:
            return {
                "provider_id": provider_id,
                "status": HealthCheckStatus.FAILED.value,
                "latency_ms": 0.0,
                "error": str(e),
            }

    def register_check_handler(
        self, provider_id: ProviderID, handler: Callable[[], HealthCheckResult]
    ) -> None:
        """Register a health check handler for a provider."""
        with self._lock:
            self._check_handlers[provider_id] = handler

    def unregister_check_handler(self, provider_id: ProviderID) -> None:
        """Unregister a health check handler for a provider."""
        with self._lock:
            self._check_handlers.pop(provider_id, None)

    def monitor(self, provider_id: ProviderID, config: Optional[HealthCheckConfig] = None) -> None:
        """Start monitoring a provider."""
        with self._lock:
            if provider_id in self._monitoring_threads:
                return
            thread = Thread(
                target=self._monitor_loop,
                args=(provider_id, config),
                daemon=True,
            )
            thread.start()
            self._monitoring_threads[provider_id] = thread

    def stop_monitoring(self, provider_id: ProviderID) -> None:
        """Stop monitoring a provider."""
        with self._lock:
            if provider_id in self._monitoring_threads:
                self._monitoring_threads[provider_id].join(timeout=1.0)
                del self._monitoring_threads[provider_id]

    def _monitor_loop(
        self, provider_id: ProviderID, config: Optional[HealthCheckConfig] = None
    ) -> None:
        """Loop for monitoring a provider."""
        check_config = config or self._config
        while self._running:
            self.check(provider_id)
            time.sleep(check_config.interval_seconds)

    def get_status(self, provider_id: ProviderID) -> Optional[ProviderHealthStatus]:
        """Get the health status for a provider."""
        return self._status.get(provider_id)

    def is_healthy(self, provider_id: ProviderID) -> bool:
        """Check if a provider is healthy."""
        status = self.get_status(provider_id)
        if status is None:
            return False
        return status.status == HealthCheckStatus.HEALTHY and not status.disabled

    def is_disabled(self, provider_id: ProviderID) -> bool:
        """Check if a provider is disabled."""
        status = self.get_status(provider_id)
        return status is not None and status.disabled

    def enable_provider(self, provider_id: ProviderID) -> None:
        """Enable a disabled provider."""
        with self._lock:
            if provider_id in self._status:
                self._status[provider_id].disabled = False
                self._status[provider_id].consecutive_failures = 0

    def disable_provider(self, provider_id: ProviderID) -> None:
        """Disable a provider."""
        with self._lock:
            if provider_id in self._status:
                self._status[provider_id].disabled = True

    def get_all_statuses(self) -> Dict[ProviderID, ProviderHealthStatus]:
        """Get health statuses for all providers."""
        return self._status.copy()

    def get_healthy_providers(self) -> List[ProviderID]:
        """Get a list of healthy provider IDs."""
        return [
            provider_id
            for provider_id, status in self._status.items()
            if status.status == HealthCheckStatus.HEALTHY and not status.disabled
        ]

    def get_degraded_providers(self) -> List[ProviderID]:
        """Get a list of degraded provider IDs."""
        return [
            provider_id
            for provider_id, status in self._status.items()
            if status.status == HealthCheckStatus.DEGRADED
        ]

    def get_failed_providers(self) -> List[ProviderID]:
        """Get a list of failed provider IDs."""
        return [
            provider_id
            for provider_id, status in self._status.items()
            if status.status == HealthCheckStatus.FAILED
        ]

    def get_disabled_providers(self) -> List[ProviderID]:
        """Get a list of disabled provider IDs."""
        return [
            provider_id
            for provider_id, status in self._status.items()
            if status.disabled
        ]

    def shutdown(self) -> None:
        """Shutdown the health monitor."""
        self._running = False
        for thread in self._monitoring_threads.values():
            thread.join(timeout=1.0)
        self._monitoring_threads.clear()
