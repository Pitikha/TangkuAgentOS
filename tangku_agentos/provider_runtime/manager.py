"""Provider manager for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import time
from threading import RLock, Thread
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..model_runtime.models import ModelConfiguration
    from .interfaces import (
        FailoverManager,
        HealthMonitor,
        LoadBalancer,
        ProviderAdapter,
        ProviderFactory,
        ProviderRegistry,
    )
    from .types import (
        HealthCheckConfig,
        HealthMetrics,
        ProviderID,
        ProviderStatus,
        RoutingPolicy,
    )

from .constants import ProviderStatus
from .exceptions import ProviderNotFoundError
from .interfaces import ProviderManager
from .registry import ProviderRegistry


class ProviderLifecycleManager:
    """Manages the lifecycle of providers (initialization, shutdown, etc.)."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._initialized: Dict[str, bool] = {}
        self._shutdown: Dict[str, bool] = {}

    def initialize_provider(self, provider_id: str, adapter: ProviderAdapter) -> None:
        """Initialize a provider."""
        with self._lock:
            if not self._initialized.get(provider_id, False):
                try:
                    adapter.initialize({})
                    self._initialized[provider_id] = True
                except Exception:
                    self._initialized[provider_id] = False
                    raise

    def shutdown_provider(self, provider_id: str, adapter: ProviderAdapter) -> None:
        """Shutdown a provider."""
        with self._lock:
            if not self._shutdown.get(provider_id, False):
                try:
                    # Placeholder for shutdown logic
                    self._shutdown[provider_id] = True
                except Exception:
                    raise

    def is_initialized(self, provider_id: str) -> bool:
        """Check if a provider is initialized."""
        return self._initialized.get(provider_id, False)


class ProviderHealthMonitor:
    """Monitors the health of providers."""

    def __init__(self, config: Optional[HealthCheckConfig] = None) -> None:
        self._config = config or HealthCheckConfig()
        self._lock = RLock()
        self._metrics: Dict[str, HealthMetrics] = {}
        self._monitoring: Dict[str, bool] = {}
        self._threads: Dict[str, Thread] = {}

    def check(self, provider_id: str, adapter: ProviderAdapter) -> HealthMetrics:
        """Perform a health check for a provider."""
        start_time = time.time()
        try:
            metrics = adapter.health_check()
            latency = (time.time() - start_time) * 1000
            return HealthMetrics(
                latency_ms=latency,
                error_rate=0.0,
                availability=1.0,
                last_check_time=time.time(),
            )
        except Exception:
            return HealthMetrics(
                latency_ms=0.0,
                error_rate=1.0,
                availability=0.0,
                last_check_time=time.time(),
            )

    def start_monitoring(self, provider_id: str, adapter: ProviderAdapter) -> None:
        """Start monitoring a provider."""
        with self._lock:
            if provider_id in self._monitoring:
                return
            self._monitoring[provider_id] = True
            thread = Thread(
                target=self._monitor_loop,
                args=(provider_id, adapter),
                daemon=True,
            )
            thread.start()
            self._threads[provider_id] = thread

    def stop_monitoring(self, provider_id: str) -> None:
        """Stop monitoring a provider."""
        with self._lock:
            self._monitoring[provider_id] = False
            if provider_id in self._threads:
                self._threads[provider_id].join(timeout=1.0)
                del self._threads[provider_id]

    def _monitor_loop(self, provider_id: str, adapter: ProviderAdapter) -> None:
        """Loop for monitoring a provider."""
        while self._monitoring.get(provider_id, False):
            metrics = self.check(provider_id, adapter)
            with self._lock:
                self._metrics[provider_id] = metrics
            time.sleep(self._config.interval_seconds)

    def get_metrics(self, provider_id: str) -> Optional[HealthMetrics]:
        """Get health metrics for a provider."""
        return self._metrics.get(provider_id)


class ProviderFailoverManager:
    """Manages failover for providers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._failures: Dict[str, int] = {}
        self._fallbacks: Dict[str, List[str]] = {}

    def record_failure(self, provider_id: str) -> None:
        """Record a failure for a provider."""
        with self._lock:
            self._failures[provider_id] = self._failures.get(provider_id, 0) + 1

    def reset(self, provider_id: str) -> None:
        """Reset the failure count for a provider."""
        with self._lock:
            self._failures[provider_id] = 0

    def get_fallback(self, provider_id: str, all_providers: List[str]) -> Optional[str]:
        """Get a fallback provider."""
        with self._lock:
            if provider_id not in self._fallbacks:
                self._fallbacks[provider_id] = [
                    p for p in all_providers if p != provider_id
                ]
            if self._fallbacks[provider_id]:
                return self._fallbacks[provider_id][0]
            return None

    def set_fallbacks(self, provider_id: str, fallbacks: List[str]) -> None:
        """Set fallback providers for a provider."""
        with self._lock:
            self._fallbacks[provider_id] = fallbacks


class ProviderLoadBalancer:
    """Load balancer for providers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._counters: Dict[str, int] = {}

    def select_provider(
        self,
        providers: List[str],
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[str]:
        """Select a provider based on the policy."""
        if not providers:
            return None
        if policy == RoutingPolicy.ROUND_ROBIN:
            return self._round_robin(providers)
        return providers[0]

    def _round_robin(self, providers: List[str]) -> str:
        """Select a provider using round-robin."""
        with self._lock:
            for provider in providers:
                self._counters[provider] = self._counters.get(provider, 0) + 1
            min_provider = min(providers, key=lambda p: self._counters.get(p, 0))
            return min_provider

    def record_request(self, provider_id: str) -> None:
        """Record a request to a provider."""
        with self._lock:
            self._counters[provider_id] = self._counters.get(provider_id, 0) + 1


class ProviderManager(ProviderManager):
    """
    Production-grade provider manager with:
    - Dynamic provider loading
    - Provider lifecycle management
    - Health monitoring
    - Automatic failover
    - Load balancing
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        factory: Optional[ProviderFactory] = None,
    ) -> None:
        self._registry = registry or ProviderRegistry()
        self._factory = factory or ProviderFactory()
        self._providers: Dict[str, ModelConfiguration] = {}
        self._adapters: Dict[str, ProviderAdapter] = {}
        self._lifecycle = ProviderLifecycleManager()
        self._health_monitor = ProviderHealthMonitor()
        self._failover = ProviderFailoverManager()
        self._load_balancer = ProviderLoadBalancer()
        self._lock = RLock()

    def add_provider(
        self,
        provider_id: str,
        configuration: ModelConfiguration,
    ) -> None:
        """Add a provider with the given configuration."""
        with self._lock:
            self._providers[provider_id] = configuration
            self._registry.register_provider(provider_id, configuration)
            adapter = self._factory.create(provider_id, configuration)
            self._adapters[provider_id] = adapter
            self._lifecycle.initialize_provider(provider_id, adapter)
            self._health_monitor.start_monitoring(provider_id, adapter)

    def get_provider(self, provider_id: str) -> ModelConfiguration:
        """Get a provider's configuration by ID."""
        return self._providers.get(provider_id) or self._registry.resolve_provider(provider_id)

    def remove_provider(self, provider_id: str) -> None:
        """Remove a provider by ID."""
        with self._lock:
            if provider_id in self._adapters:
                self._health_monitor.stop_monitoring(provider_id)
                self._lifecycle.shutdown_provider(provider_id, self._adapters[provider_id])
            self._providers.pop(provider_id, None)
            self._adapters.pop(provider_id, None)
            self._registry.unregister_provider(provider_id)

    def list_providers(self) -> List[str]:
        """List all registered provider IDs."""
        return sorted(self._providers.keys())

    def get_adapter(self, provider_id: str) -> Optional[ProviderAdapter]:
        """Get a provider's adapter by ID."""
        return self._adapters.get(provider_id)

    def get_health_metrics(self, provider_id: str) -> Optional[HealthMetrics]:
        """Get health metrics for a provider."""
        return self._health_monitor.get_metrics(provider_id)

    def get_fallback(self, provider_id: str) -> Optional[str]:
        """Get a fallback provider for the given provider."""
        return self._failover.get_fallback(provider_id, self.list_providers())

    def select_provider(
        self,
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[str]:
        """Select a provider based on the policy."""
        return self._load_balancer.select_provider(self.list_providers(), policy)

    def record_failure(self, provider_id: str) -> None:
        """Record a failure for a provider."""
        self._failover.record_failure(provider_id)

    def record_request(self, provider_id: str) -> None:
        """Record a request to a provider."""
        self._load_balancer.record_request(provider_id)

    def get_status(self, provider_id: str) -> ProviderStatus:
        """Get the status of a provider."""
        if provider_id not in self._providers:
            raise ProviderNotFoundError(f"Provider {provider_id} not found")
        if self._failover._failures.get(provider_id, 0) >= 3:
            return ProviderStatus.FAILED
        metrics = self._health_monitor.get_metrics(provider_id)
        if metrics is None:
            return ProviderStatus.UNREGISTERED
        if metrics.availability < 0.5:
            return ProviderStatus.DEGRADED
        return ProviderStatus.HEALTHY
