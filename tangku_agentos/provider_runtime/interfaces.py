"""Interfaces for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..model_runtime.models import ModelConfiguration
    from .types import (
        APIKey,
        BenchmarkConfig,
        BenchmarkMetrics,
        HealthCheckConfig,
        HealthMetrics,
        ModelDefinition,
        ModelID,
        ProviderCapability,
        ProviderDefinition,
        ProviderID,
        ProviderRequest,
        ProviderResponse,
        ProviderSettings,
        ProviderStatus,
        RateLimitConfig,
        RetryConfig,
        RoutingPolicy,
        SessionID,
        UsageMetrics,
    )


# --- Core Interfaces ---
class ProviderRegistryInterface(ABC):
    """Interface for provider registry operations."""

    @abstractmethod
    def register_provider(
        self, provider_id: ProviderID, configuration: ModelConfiguration
    ) -> None:
        """Register a provider with the given configuration."""
        ...

    @abstractmethod
    def resolve_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """Resolve a provider's configuration by ID."""
        ...

    @abstractmethod
    def list_providers(self) -> List[ProviderID]:
        """List all registered provider IDs."""
        ...

    @abstractmethod
    def unregister_provider(self, provider_id: ProviderID) -> None:
        """Unregister a provider by ID."""
        ...


class ProviderManager(ABC):
    """Interface for provider runtime management."""

    @abstractmethod
    def add_provider(
        self, provider_id: ProviderID, configuration: ModelConfiguration
    ) -> None:
        """Add a provider with the given configuration."""
        ...

    @abstractmethod
    def get_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """Get a provider's configuration by ID."""
        ...

    @abstractmethod
    def remove_provider(self, provider_id: ProviderID) -> None:
        """Remove a provider by ID."""
        ...

    @abstractmethod
    def list_providers(self) -> List[ProviderID]:
        """List all registered provider IDs."""
        ...

    @abstractmethod
    def get_adapter(self, provider_id: ProviderID) -> Any:
        """Get a provider's adapter by ID."""
        ...


class ProviderAdapter(ABC):
    """Interface for provider adapter abstraction."""

    @property
    @abstractmethod
    def provider_id(self) -> ProviderID:
        """Get the provider ID."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Get the provider's capabilities."""
        ...

    @abstractmethod
    def initialize(self, settings: ProviderSettings) -> None:
        """Initialize the provider adapter."""
        ...

    @abstractmethod
    def send(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider."""
        ...

    @abstractmethod
    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider asynchronously."""
        ...

    @abstractmethod
    def supports(self, capability: ProviderCapability) -> bool:
        """Check if the provider supports a capability."""
        ...

    @abstractmethod
    def health_check(self) -> HealthMetrics:
        """Perform a health check."""
        ...


class ProviderFactory(ABC):
    """Interface for provider instance creation."""

    @abstractmethod
    def create(
        self, provider_id: ProviderID, configuration: ModelConfiguration
    ) -> ProviderAdapter:
        """Create a provider adapter for the given ID and configuration."""
        ...


class ProviderConfiguration(ABC):
    """Interface for provider configuration."""

    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get the provider configuration."""
        ...

    @abstractmethod
    def get_secret(self, provider_id: ProviderID) -> Optional[APIKey]:
        """Get the API key for a provider."""
        ...


class ProviderHealth(ABC):
    """Interface for provider health checks."""

    @abstractmethod
    def check(self, provider_id: ProviderID) -> Dict[str, Any]:
        """Perform a health check for a provider."""
        ...

    @abstractmethod
    def monitor(self, provider_id: ProviderID, config: HealthCheckConfig) -> None:
        """Start monitoring a provider."""
        ...

    @abstractmethod
    def stop_monitoring(self, provider_id: ProviderID) -> None:
        """Stop monitoring a provider."""
        ...


class ProviderSession(ABC):
    """Interface for provider session management."""

    @abstractmethod
    def start(self, provider_id: ProviderID, model_id: Optional[ModelID] = None) -> SessionID:
        """Start a new session with a provider."""
        ...

    @abstractmethod
    def end(self, session_id: SessionID) -> None:
        """End a session by ID."""
        ...

    @abstractmethod
    def get_session(self, session_id: SessionID) -> Dict[str, Any]:
        """Get a session by ID."""
        ...


# --- Routing Interfaces ---
class ProviderRouter(ABC):
    """Interface for routing requests to providers."""

    @abstractmethod
    def route(
        self,
        request: ProviderRequest,
        policy: Optional[RoutingPolicy] = None,
    ) -> ProviderID:
        """Route a request to a provider based on the policy."""
        ...

    @abstractmethod
    def select_provider(
        self,
        task: str,
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[ProviderID]:
        """Select a provider for a task based on the policy."""
        ...


class LoadBalancer(ABC):
    """Interface for load balancing."""

    @abstractmethod
    def select_provider(
        self,
        providers: List[ProviderID],
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[ProviderID]:
        """Select a provider based on the policy."""
        ...

    @abstractmethod
    def record_request(self, provider_id: ProviderID) -> None:
        """Record a request to a provider."""
        ...


class FailoverManager(ABC):
    """Interface for failover management."""

    @abstractmethod
    def get_fallback(self, provider_id: ProviderID) -> Optional[ProviderID]:
        """Get a fallback provider."""
        ...

    @abstractmethod
    def record_failure(self, provider_id: ProviderID) -> None:
        """Record a failure for a provider."""
        ...

    @abstractmethod
    def reset(self, provider_id: ProviderID) -> None:
        """Reset the failure count for a provider."""
        ...


# --- Retry Interfaces ---
class RetryManager(ABC):
    """Interface for retry management."""

    @abstractmethod
    def should_retry(self, attempt: int, config: RetryConfig) -> bool:
        """Check if a request should be retried."""
        ...

    @abstractmethod
    def get_delay(self, attempt: int, config: RetryConfig) -> float:
        """Get the delay before the next retry."""
        ...


# --- Rate Limit Interfaces ---
class RateLimitManager(ABC):
    """Interface for rate limiting."""

    @abstractmethod
    def is_allowed(self, provider_id: ProviderID) -> bool:
        """Check if a request is allowed for a provider."""
        ...

    @abstractmethod
    def record_request(self, provider_id: ProviderID) -> None:
        """Record a request for a provider."""
        ...

    @abstractmethod
    def configure(self, provider_id: ProviderID, config: RateLimitConfig) -> None:
        """Configure rate limiting for a provider."""
        ...


# --- Key Management Interfaces ---
class KeyManager(ABC):
    """Interface for API key management."""

    @abstractmethod
    def save_key(self, provider_id: ProviderID, key: APIKey) -> None:
        """Save an API key for a provider."""
        ...

    @abstractmethod
    def get_key(self, provider_id: ProviderID) -> Optional[APIKey]:
        """Get the API key for a provider."""
        ...

    @abstractmethod
    def remove_key(self, provider_id: ProviderID) -> None:
        """Remove the API key for a provider."""
        ...

    @abstractmethod
    def rotate_key(self, provider_id: ProviderID, new_key: APIKey) -> None:
        """Rotate the API key for a provider."""
        ...

    @abstractmethod
    def list_keys(self) -> List[ProviderID]:
        """List all provider IDs with stored keys."""
        ...


# --- Benchmark Interfaces ---
class BenchmarkManager(ABC):
    """Interface for benchmarking providers."""

    @abstractmethod
    def run_benchmark(
        self,
        provider_ids: Optional[List[ProviderID]] = None,
        config: Optional[BenchmarkConfig] = None,
    ) -> Dict[ProviderID, BenchmarkMetrics]:
        """Run a benchmark for the given providers."""
        ...

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the benchmark history."""
        ...


# --- Plugin Interfaces ---
class ProviderPlugin(ABC):
    """Interface for provider plugins."""

    @property
    @abstractmethod
    def provider_id(self) -> ProviderID:
        """Get the plugin's provider ID."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get the plugin's display name."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Get the plugin's capabilities."""
        ...

    @abstractmethod
    def initialize(self, settings: ProviderSettings) -> None:
        """Initialize the plugin."""
        ...

    @abstractmethod
    def send(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider."""
        ...

    @abstractmethod
    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider asynchronously."""
        ...

    @abstractmethod
    def supports(self, capability: ProviderCapability) -> bool:
        """Check if the plugin supports a capability."""
        ...

    @abstractmethod
    def health_check(self) -> HealthMetrics:
        """Perform a health check."""
        ...


class PluginLoader(ABC):
    """Interface for loading provider plugins."""

    @abstractmethod
    def load_plugin(self, plugin_path: str) -> ProviderPlugin:
        """Load a plugin from the given path."""
        ...

    @abstractmethod
    def load_all_plugins(self, directory: str) -> List[ProviderPlugin]:
        """Load all plugins from a directory."""
        ...

    @abstractmethod
    def unload_plugin(self, plugin_id: ProviderID) -> None:
        """Unload a plugin by ID."""
        ...
