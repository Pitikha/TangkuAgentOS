"""
TangkuAgentOS Provider Runtime - Core Interfaces

This module defines the abstract base classes (ABCs), protocols, and interfaces
for all providers, adapters, managers, and utilities in the Provider Runtime.
It ensures consistency, extensibility, and type safety across the entire package.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    runtime_checkable,
    TypedDict,
    Union,
)


# =============================================================================
# Type Definitions
# =============================================================================

# Provider and Model Types
ProviderName = str
ProviderID = str
ModelID = str
SessionID = str

# Capabilities
ProviderCapability = Literal[
    "text",
    "chat",
    "vision",
    "audio",
    "video",
    "embedding",
    "classification",
    "summarization",
    "translation",
    "code_execution",
    "tool_use",
    "streaming",
    "batch",
    "fine_tuning",
]

# Status Types
ProviderStatus = Literal[
    "unregistered",
    "registered",
    "initialized",
    "healthy",
    "unhealthy",
    "disabled",
    "deprecated",
]

ProviderType = Literal[
    "cloud",
    "local",
    "hybrid",
    "custom",
]


# =============================================================================
# Request/Response Types (TypedDict for better type safety)
# =============================================================================

class ProviderRequest(TypedDict, total=False):
    """Generic request payload for providers."""

    prompt: Optional[str]
    messages: Optional[List[Dict[str, Any]]]
    model: Optional[ModelID]
    temperature: Optional[float]
    max_tokens: Optional[int]
    top_p: Optional[float]
    top_k: Optional[int]
    stream: Optional[bool]
    stop: Optional[List[str]]
    presence_penalty: Optional[float]
    frequency_penalty: Optional[float]
    user: Optional[str]
    extra: Optional[Dict[str, Any]]


class ProviderResponse(TypedDict, total=False):
    """Generic response payload from providers."""

    content: Optional[str]
    model: Optional[ModelID]
    finish_reason: Optional[str]
    usage: Optional[Dict[str, Any]]
    logprobs: Optional[Dict[str, Any]]
    choices: Optional[List[Dict[str, Any]]]
    embeddings: Optional[List[List[float]]]
    error: Optional[Dict[str, Any]]
    extra: Optional[Dict[str, Any]]


class StreamChunk(TypedDict, total=False):
    """Chunk of a streaming response."""

    content: Optional[str]
    finish_reason: Optional[str]
    usage: Optional[Dict[str, Any]]
    model: Optional[ModelID]
    extra: Optional[Dict[str, Any]]


# Configuration Types
class ProviderSettings(TypedDict, total=False):
    """Settings for a provider."""

    api_key: Optional[str]
    base_url: Optional[str]
    timeout: Optional[float]
    max_retries: Optional[int]
    retry_delay: Optional[float]
    rate_limit: Optional[int]
    headers: Optional[Dict[str, str]]
    extra: Optional[Dict[str, Any]]


class ModelConfiguration(TypedDict, total=False):
    """Configuration for a model."""

    model_id: Optional[ModelID]
    provider_id: Optional[ProviderID]
    settings: Optional[ProviderSettings]
    capabilities: Optional[Dict[ProviderCapability, bool]]
    metadata: Optional[Dict[str, Any]]


class ProviderDefinition(TypedDict, total=False):
    """Definition of a provider."""

    provider_id: ProviderID
    display_name: str
    provider_type: ProviderType
    capabilities: Dict[ProviderCapability, bool]
    models: List[ModelID]
    metadata: Dict[str, Any]


# Routing Types
class RoutingPolicy(TypedDict, total=False):
    """Policy for routing requests."""

    strategy: Literal["capability", "cost", "latency", "quality", "random", "weighted"]
    fallback_enabled: bool
    max_parallel: int
    circuit_breaker_threshold: int
    weights: Optional[Dict[ProviderID, float]]


# Health and Benchmark Types
class HealthCheckConfig(TypedDict, total=False):
    """Configuration for health checks."""

    interval: float
    timeout: float
    max_retries: int


class HealthMetrics(TypedDict, total=False):
    """Metrics from a health check."""

    status: ProviderStatus
    latency: Optional[float]
    error: Optional[str]
    timestamp: Optional[float]


class BenchmarkConfig(TypedDict, total=False):
    """Configuration for benchmarking."""

    tasks: List[str]
    iterations: int
    metrics: List[str]


class BenchmarkMetrics(TypedDict, total=False):
    """Metrics from a benchmark."""

    latency_avg: Optional[float]
    latency_std: Optional[float]
    cost_total: Optional[float]
    tokens_total: Optional[int]
    success_rate: Optional[float]
    quality_score: Optional[float]


# Rate Limiting Types
class RateLimitConfig(TypedDict, total=False):
    """Configuration for rate limiting."""

    requests_per_minute: int
    burst_size: int
    enabled: bool


# Retry Types
class RetryConfig(TypedDict, total=False):
    """Configuration for retries."""

    max_attempts: int
    base_delay: float
    max_delay: float
    exponential_backoff: bool
    retryable_errors: List[str]


# Usage and Quota Types
class UsageMetrics(TypedDict, total=False):
    """Usage metrics for a provider."""

    requests_total: int
    tokens_total: int
    cost_total: float
    errors_total: int


class QuotaConfig(TypedDict, total=False):
    """Quota configuration for a provider."""

    max_requests: Optional[int]
    max_tokens: Optional[int]
    max_cost: Optional[float]
    reset_interval: Optional[float]  # in seconds


# API Key Types
APIKey = str


# =============================================================================
# Core Interfaces (ABCs)
# =============================================================================

class ProviderRegistryInterface(ABC):
    """
    Interface for provider registry operations.

    This interface defines the contract for registering, resolving, and managing
    providers in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def register_provider(
        self,
        provider_id: ProviderID,
        configuration: ModelConfiguration,
        definition: Optional[ProviderDefinition] = None,
    ) -> None:
        """
        Register a provider with the given configuration and definition.

        Args:
            provider_id: Unique identifier for the provider.
            configuration: Configuration for the provider.
            definition: Optional definition of the provider.

        Raises:
            ProviderAlreadyExistsError: If the provider is already registered.
        """
        ...

    @abstractmethod
    def resolve_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """
        Resolve a provider's configuration by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ModelConfiguration: The provider's configuration.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        ...

    @abstractmethod
    def list_providers(self) -> List[ProviderID]:
        """
        List all registered provider IDs.

        Returns:
            List[ProviderID]: List of all registered provider IDs.
        """
        ...

    @abstractmethod
    def unregister_provider(self, provider_id: ProviderID) -> None:
        """
        Unregister a provider by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        ...

    @abstractmethod
    def get_definition(self, provider_id: ProviderID) -> Optional[ProviderDefinition]:
        """
        Get the definition for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[ProviderDefinition]: The provider's definition, or None if not found.
        """
        ...

    @abstractmethod
    def get_status(self, provider_id: ProviderID) -> ProviderStatus:
        """
        Get the status for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ProviderStatus: The current status of the provider.
        """
        ...

    @abstractmethod
    def set_status(self, provider_id: ProviderID, status: ProviderStatus) -> None:
        """
        Set the status for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            status: New status for the provider.
        """
        ...

    @abstractmethod
    def get_capabilities(self, provider_id: ProviderID) -> Dict[ProviderCapability, bool]:
        """
        Get the capabilities for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Dict[ProviderCapability, bool]: Dictionary of capabilities and their availability.
        """
        ...

    @abstractmethod
    def has_capability(self, provider_id: ProviderID, capability: ProviderCapability) -> bool:
        """
        Check if a provider has a specific capability.

        Args:
            provider_id: Unique identifier for the provider.
            capability: Capability to check.

        Returns:
            bool: True if the provider has the capability, False otherwise.
        """
        ...

    @abstractmethod
    def filter_by_capability(self, capability: ProviderCapability) -> List[ProviderID]:
        """
        Filter providers by a specific capability.

        Args:
            capability: Capability to filter by.

        Returns:
            List[ProviderID]: List of provider IDs that have the capability.
        """
        ...


class ProviderManager(ABC):
    """
    Interface for provider runtime management.

    This interface defines the contract for managing provider instances,
    including adding, removing, and retrieving providers.
    """

    @abstractmethod
    def add_provider(
        self, provider_id: ProviderID, configuration: ModelConfiguration
    ) -> None:
        """
        Add a provider with the given configuration.

        Args:
            provider_id: Unique identifier for the provider.
            configuration: Configuration for the provider.
        """
        ...

    @abstractmethod
    def get_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """
        Get a provider's configuration by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ModelConfiguration: The provider's configuration.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        ...

    @abstractmethod
    def remove_provider(self, provider_id: ProviderID) -> None:
        """
        Remove a provider by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        ...

    @abstractmethod
    def list_providers(self) -> List[ProviderID]:
        """
        List all registered provider IDs.

        Returns:
            List[ProviderID]: List of all registered provider IDs.
        """
        ...

    @abstractmethod
    def get_adapter(self, provider_id: ProviderID) -> Any:
        """
        Get a provider's adapter by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Any: The provider's adapter instance.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        ...


# =============================================================================
# Provider and Adapter Interfaces
# =============================================================================

class ProviderAdapter(ABC):
    """
    Interface for provider adapter abstraction.

    Adapters normalize provider-specific APIs into a generic format
    for use by the TangkuAgentOS Provider Runtime.
    """

    @property
    @abstractmethod
    def provider_id(self) -> ProviderID:
        """
        Get the provider ID.

        Returns:
            ProviderID: Unique identifier for the provider.
        """
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """
        Get the provider's capabilities.

        Returns:
            Dict[ProviderCapability, bool]: Dictionary of capabilities and their availability.
        """
        ...

    @abstractmethod
    def initialize(self, settings: ProviderSettings) -> None:
        """
        Initialize the provider adapter.

        Args:
            settings: Settings for the provider.
        """
        ...

    @abstractmethod
    async def initialize_async(self, settings: ProviderSettings) -> None:
        """
        Initialize the provider adapter asynchronously.

        Args:
            settings: Settings for the provider.
        """
        ...

    @abstractmethod
    def send(self, request: ProviderRequest) -> ProviderResponse:
        """
        Send a request to the provider synchronously.

        Args:
            request: Request payload.

        Returns:
            ProviderResponse: Response from the provider.
        """
        ...

    @abstractmethod
    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """
        Send a request to the provider asynchronously.

        Args:
            request: Request payload.

        Returns:
            ProviderResponse: Response from the provider.
        """
        ...

    @abstractmethod
    async def send_stream(
        self, request: ProviderRequest
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a request to the provider and stream the response.

        Args:
            request: Request payload.

        Yields:
            StreamChunk: Chunks of the streaming response.
        """
        ...

    @abstractmethod
    def supports(self, capability: ProviderCapability) -> bool:
        """
        Check if the provider supports a capability.

        Args:
            capability: Capability to check.

        Returns:
            bool: True if the provider supports the capability, False otherwise.
        """
        ...

    @abstractmethod
    def health_check(self) -> HealthMetrics:
        """
        Perform a health check on the provider.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...

    @abstractmethod
    async def health_check_async(self) -> HealthMetrics:
        """
        Perform a health check on the provider asynchronously.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Clean up resources used by the adapter."""
        ...


class ProviderFactory(ABC):
    """
    Interface for provider instance creation.

    This interface defines the contract for creating provider adapters
    for the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def create(
        self, provider_id: ProviderID, configuration: ModelConfiguration
    ) -> ProviderAdapter:
        """
        Create a provider adapter for the given ID and configuration.

        Args:
            provider_id: Unique identifier for the provider.
            configuration: Configuration for the provider.

        Returns:
            ProviderAdapter: The created provider adapter.

        Raises:
            ProviderNotFoundError: If the provider is not supported.
        """
        ...


# =============================================================================
# Health and Benchmark Interfaces
# =============================================================================

class ProviderHealth(ABC):
    """
    Interface for provider health checks.

    This interface defines the contract for monitoring and checking
    the health of providers in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def check(self, provider_id: ProviderID) -> HealthMetrics:
        """
        Perform a health check for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...

    @abstractmethod
    async def check_async(self, provider_id: ProviderID) -> HealthMetrics:
        """
        Perform a health check for a provider asynchronously.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...

    @abstractmethod
    def monitor(
        self, provider_id: ProviderID, config: HealthCheckConfig
    ) -> None:
        """
        Start monitoring a provider.

        Args:
            provider_id: Unique identifier for the provider.
            config: Configuration for health checks.
        """
        ...

    @abstractmethod
    def stop_monitoring(self, provider_id: ProviderID) -> None:
        """
        Stop monitoring a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...


class BenchmarkManager(ABC):
    """
    Interface for benchmarking providers.

    This interface defines the contract for running benchmarks on
    providers in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def run_benchmark(
        self,
        provider_ids: Optional[List[ProviderID]] = None,
        config: Optional[BenchmarkConfig] = None,
    ) -> Dict[ProviderID, BenchmarkMetrics]:
        """
        Run a benchmark for the given providers.

        Args:
            provider_ids: List of provider IDs to benchmark. If None, benchmark all providers.
            config: Configuration for the benchmark.

        Returns:
            Dict[ProviderID, BenchmarkMetrics]: Benchmark results for each provider.
        """
        ...

    @abstractmethod
    async def run_benchmark_async(
        self,
        provider_ids: Optional[List[ProviderID]] = None,
        config: Optional[BenchmarkConfig] = None,
    ) -> Dict[ProviderID, BenchmarkMetrics]:
        """
        Run a benchmark for the given providers asynchronously.

        Args:
            provider_ids: List of provider IDs to benchmark. If None, benchmark all providers.
            config: Configuration for the benchmark.

        Returns:
            Dict[ProviderID, BenchmarkMetrics]: Benchmark results for each provider.
        """
        ...

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the benchmark history.

        Returns:
            List[Dict[str, Any]]: List of past benchmark results.
        """
        ...


# =============================================================================
# Routing Interfaces
# =============================================================================

class ProviderRouter(ABC):
    """
    Interface for routing requests to providers.

    This interface defines the contract for routing requests to the
    most appropriate provider based on policies and capabilities.
    """

    @abstractmethod
    def route(
        self,
        request: ProviderRequest,
        policy: Optional[RoutingPolicy] = None,
    ) -> ProviderID:
        """
        Route a request to a provider based on the policy.

        Args:
            request: Request payload.
            policy: Optional routing policy.

        Returns:
            ProviderID: ID of the selected provider.
        """
        ...

    @abstractmethod
    async def route_async(
        self,
        request: ProviderRequest,
        policy: Optional[RoutingPolicy] = None,
    ) -> ProviderID:
        """
        Route a request to a provider asynchronously.

        Args:
            request: Request payload.
            policy: Optional routing policy.

        Returns:
            ProviderID: ID of the selected provider.
        """
        ...

    @abstractmethod
    def select_provider(
        self,
        task: str,
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[ProviderID]:
        """
        Select a provider for a task based on the policy.

        Args:
            task: Description of the task.
            policy: Optional routing policy.

        Returns:
            Optional[ProviderID]: ID of the selected provider, or None if no provider is available.
        """
        ...

    @abstractmethod
    async def select_provider_async(
        self,
        task: str,
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[ProviderID]:
        """
        Select a provider for a task asynchronously.

        Args:
            task: Description of the task.
            policy: Optional routing policy.

        Returns:
            Optional[ProviderID]: ID of the selected provider, or None if no provider is available.
        """
        ...


class LoadBalancer(ABC):
    """
    Interface for load balancing.

    This interface defines the contract for load balancing requests
    across multiple providers.
    """

    @abstractmethod
    def select_provider(
        self,
        providers: List[ProviderID],
        policy: Optional[RoutingPolicy] = None,
    ) -> Optional[ProviderID]:
        """
        Select a provider based on the policy.

        Args:
            providers: List of provider IDs to choose from.
            policy: Optional routing policy.

        Returns:
            Optional[ProviderID]: ID of the selected provider, or None if no provider is available.
        """
        ...

    @abstractmethod
    def record_request(self, provider_id: ProviderID) -> None:
        """
        Record a request to a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...


class FailoverManager(ABC):
    """
    Interface for failover management.

    This interface defines the contract for managing failover behavior
    when a provider fails to handle a request.
    """

    @abstractmethod
    def get_fallback(self, provider_id: ProviderID) -> Optional[ProviderID]:
        """
        Get a fallback provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[ProviderID]: ID of the fallback provider, or None if no fallback is available.
        """
        ...

    @abstractmethod
    def record_failure(self, provider_id: ProviderID) -> None:
        """
        Record a failure for a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...

    @abstractmethod
    def reset(self, provider_id: ProviderID) -> None:
        """
        Reset the failure count for a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...


# =============================================================================
# Retry and Rate Limit Interfaces
# =============================================================================

class RetryManager(ABC):
    """
    Interface for retry management.

    This interface defines the contract for managing retries of failed
    requests to providers.
    """

    @abstractmethod
    def should_retry(self, attempt: int, config: RetryConfig) -> bool:
        """
        Check if a request should be retried.

        Args:
            attempt: Current attempt number.
            config: Retry configuration.

        Returns:
            bool: True if the request should be retried, False otherwise.
        """
        ...

    @abstractmethod
    def get_delay(self, attempt: int, config: RetryConfig) -> float:
        """
        Get the delay before the next retry.

        Args:
            attempt: Current attempt number.
            config: Retry configuration.

        Returns:
            float: Delay in seconds before the next retry.
        """
        ...


class RateLimitManager(ABC):
    """
    Interface for rate limiting.

    This interface defines the contract for managing rate limits for
    requests to providers.
    """

    @abstractmethod
    def is_allowed(self, provider_id: ProviderID) -> bool:
        """
        Check if a request is allowed for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        ...

    @abstractmethod
    def record_request(self, provider_id: ProviderID) -> None:
        """
        Record a request for a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...

    @abstractmethod
    def configure(self, provider_id: ProviderID, config: RateLimitConfig) -> None:
        """
        Configure rate limiting for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            config: Rate limit configuration.
        """
        ...


# =============================================================================
# Key Management Interfaces
# =============================================================================

class KeyManager(ABC):
    """
    Interface for API key management.

    This interface defines the contract for managing API keys for
    providers in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def save_key(self, provider_id: ProviderID, key: APIKey) -> None:
        """
        Save an API key for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            key: API key to save.
        """
        ...

    @abstractmethod
    def get_key(self, provider_id: ProviderID) -> Optional[APIKey]:
        """
        Get the API key for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[APIKey]: The API key, or None if not found.
        """
        ...

    @abstractmethod
    def remove_key(self, provider_id: ProviderID) -> None:
        """
        Remove the API key for a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        ...

    @abstractmethod
    def rotate_key(self, provider_id: ProviderID, new_key: APIKey) -> None:
        """
        Rotate the API key for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            new_key: New API key to set.
        """
        ...

    @abstractmethod
    def list_keys(self) -> List[ProviderID]:
        """
        List all provider IDs with stored keys.

        Returns:
            List[ProviderID]: List of provider IDs with stored keys.
        """
        ...


# =============================================================================
# Session Management Interfaces
# =============================================================================

class ProviderSession(ABC):
    """
    Interface for provider session management.

    This interface defines the contract for managing sessions with
    providers in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def start(self, provider_id: ProviderID, model_id: Optional[ModelID] = None) -> SessionID:
        """
        Start a new session with a provider.

        Args:
            provider_id: Unique identifier for the provider.
            model_id: Optional model ID for the session.

        Returns:
            SessionID: Unique identifier for the session.
        """
        ...

    @abstractmethod
    def end(self, session_id: SessionID) -> None:
        """
        End a session by ID.

        Args:
            session_id: Unique identifier for the session.
        """
        ...

    @abstractmethod
    def get_session(self, session_id: SessionID) -> Dict[str, Any]:
        """
        Get a session by ID.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            Dict[str, Any]: Session data.
        """
        ...


# =============================================================================
# Plugin Interfaces
# =============================================================================

class ProviderPlugin(ABC):
    """
    Interface for provider plugins.

    This interface defines the contract for provider plugins in the
    TangkuAgentOS Provider Runtime.
    """

    @property
    @abstractmethod
    def provider_id(self) -> ProviderID:
        """
        Get the plugin's provider ID.

        Returns:
            ProviderID: Unique identifier for the provider.
        """
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Get the plugin's display name.

        Returns:
            str: Human-readable name for the plugin.
        """
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """
        Get the plugin's capabilities.

        Returns:
            Dict[ProviderCapability, bool]: Dictionary of capabilities and their availability.
        """
        ...

    @abstractmethod
    def initialize(self, settings: ProviderSettings) -> None:
        """
        Initialize the plugin.

        Args:
            settings: Settings for the provider.
        """
        ...

    @abstractmethod
    async def initialize_async(self, settings: ProviderSettings) -> None:
        """
        Initialize the plugin asynchronously.

        Args:
            settings: Settings for the provider.
        """
        ...

    @abstractmethod
    def send(self, request: ProviderRequest) -> ProviderResponse:
        """
        Send a request to the provider.

        Args:
            request: Request payload.

        Returns:
            ProviderResponse: Response from the provider.
        """
        ...

    @abstractmethod
    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """
        Send a request to the provider asynchronously.

        Args:
            request: Request payload.

        Returns:
            ProviderResponse: Response from the provider.
        """
        ...

    @abstractmethod
    async def send_stream(
        self, request: ProviderRequest
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a request to the provider and stream the response.

        Args:
            request: Request payload.

        Yields:
            StreamChunk: Chunks of the streaming response.
        """
        ...

    @abstractmethod
    def supports(self, capability: ProviderCapability) -> bool:
        """
        Check if the plugin supports a capability.

        Args:
            capability: Capability to check.

        Returns:
            bool: True if the plugin supports the capability, False otherwise.
        """
        ...

    @abstractmethod
    def health_check(self) -> HealthMetrics:
        """
        Perform a health check on the plugin.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...

    @abstractmethod
    async def health_check_async(self) -> HealthMetrics:
        """
        Perform a health check on the plugin asynchronously.

        Returns:
            HealthMetrics: Metrics from the health check.
        """
        ...


class PluginLoader(ABC):
    """
    Interface for loading provider plugins.

    This interface defines the contract for loading and managing
    provider plugins in the TangkuAgentOS Provider Runtime.
    """

    @abstractmethod
    def load_plugin(self, plugin_path: str) -> ProviderPlugin:
        """
        Load a plugin from the given path.

        Args:
            plugin_path: Path to the plugin file.

        Returns:
            ProviderPlugin: The loaded plugin instance.

        Raises:
            PluginLoadError: If the plugin cannot be loaded.
        """
        ...

    @abstractmethod
    def load_all_plugins(self, directory: str) -> List[ProviderPlugin]:
        """
        Load all plugins from a directory.

        Args:
            directory: Path to the directory containing plugins.

        Returns:
            List[ProviderPlugin]: List of loaded plugin instances.
        """
        ...

    @abstractmethod
    def unload_plugin(self, plugin_id: ProviderID) -> None:
        """
        Unload a plugin by ID.

        Args:
            plugin_id: Unique identifier for the plugin.
        """
        ...


# =============================================================================
# Protocol Definitions (Structural Subtyping)
# =============================================================================

@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol for all AI Providers (structural subtyping)."""

    @property
    def provider_id(self) -> ProviderID:
        """Unique identifier for the provider."""
        ...

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Supported capabilities."""
        ...

    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request asynchronously."""
        ...

    async def send_stream(self, request: ProviderRequest) -> AsyncIterator[StreamChunk]:
        """Send a request and stream the response."""
        ...

    def health_check(self) -> HealthMetrics:
        """Perform a health check."""
        ...


@runtime_checkable
class AdapterProtocol(Protocol):
    """Protocol for Provider Adapters (structural subtyping)."""

    @property
    def provider_id(self) -> ProviderID:
        """Unique identifier for the provider."""
        ...

    async def adapt_request(self, request: ProviderRequest) -> ProviderRequest:
        """Transform a generic request into a provider-specific format."""
        ...

    async def adapt_response(self, response: ProviderResponse) -> ProviderResponse:
        """Transform a provider-specific response into a generic format."""
        ...
