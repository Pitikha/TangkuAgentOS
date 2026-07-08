"""Type definitions for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
    TypedDict,
    Union,
)


# --- Core Types ---
ProviderID = str
ModelID = str
SessionID = str
RequestID = str
APIKey = str


# --- Enums ---
class ProviderType(Enum):
    """Types of AI providers."""

    CLOUD = "cloud"
    LOCAL = "local"
    CUSTOM = "custom"
    PLUGIN = "plugin"


class ProviderStatus(Enum):
    """Status of a provider."""

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


class ProviderCapability(Enum):
    """Capabilities supported by providers."""

    CHAT = "chat"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"
    VISION = "vision"
    AUDIO = "audio"
    IMAGE_GENERATION = "image_generation"
    TOOL_CALLING = "tool_calling"
    FUNCTION_CALLING = "function_calling"
    REASONING = "reasoning"
    JSON_MODE = "json_mode"
    STRUCTURED_OUTPUT = "structured_output"
    OFFLINE = "offline"


class RoutingPolicy(Enum):
    """Policies for routing requests to providers."""

    COST = "cost"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    CAPABILITY = "capability"
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    PRIORITY = "priority"


class LoadBalancingStrategy(Enum):
    """Strategies for load balancing."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"


class RetryPolicy(Enum):
    """Policies for retrying failed requests."""

    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    JITTER = "jitter"


class RateLimitStrategy(Enum):
    """Strategies for rate limiting."""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


class HealthCheckStatus(Enum):
    """Status of a health check."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    TIMEOUT = "timeout"


# --- TypedDicts ---
class ProviderSettings(TypedDict, total=False):
    """Settings for a provider."""

    api_key: APIKey
    base_url: str
    timeout: float
    max_retries: int
    headers: Dict[str, str]
    organization: str
    project: str
    region: str


class ProviderMetadata(TypedDict, total=False):
    """Metadata for a provider."""

    display_name: str
    description: str
    version: str
    author: str
    license: str
    homepage: str


class ModelMetadata(TypedDict, total=False):
    """Metadata for a model."""

    display_name: str
    family: str
    context_length: int
    pricing: Dict[str, float]
    vision: bool
    reasoning: bool
    tools: bool
    embeddings: bool
    audio: bool
    image: bool
    streaming: bool
    json_mode: bool
    structured_output: bool
    recommended_tasks: List[str]
    speed: str
    quality: str
    offline_availability: bool
    memory_usage: str


class ProviderCapabilities(TypedDict, total=False):
    """Capabilities of a provider."""

    chat: bool
    streaming: bool
    embeddings: bool
    vision: bool
    audio: bool
    image_generation: bool
    tool_calling: bool
    function_calling: bool
    reasoning: bool
    json_mode: bool
    structured_output: bool
    offline: bool


class RequestParameters(TypedDict, total=False):
    """Parameters for a provider request."""

    model: ModelID
    temperature: float
    max_tokens: int
    top_p: float
    top_k: int
    stop: List[str]
    presence_penalty: float
    frequency_penalty: float
    stream: bool
    image: bool
    tool_calls: List[Dict[str, Any]]


class UsageMetrics(TypedDict, total=False):
    """Usage metrics for a provider."""

    total_requests: int
    total_tokens: int
    total_cost: float
    last_request_time: float


class HealthMetrics(TypedDict, total=False):
    """Health metrics for a provider."""

    latency_ms: float
    error_rate: float
    availability: float
    last_check_time: float


class BenchmarkMetrics(TypedDict, total=False):
    """Benchmark metrics for a provider."""

    latency_ms: float
    tokens_per_second: float
    reliability: float
    cost_per_token: float
    quality_score: float


# --- Dataclasses ---
@dataclass
class ProviderDefinition:
    """Definition of a provider."""

    provider_id: ProviderID
    display_name: str
    provider_type: ProviderType = ProviderType.CLOUD
    capabilities: Dict[ProviderCapability, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelDefinition:
    """Definition of a model."""

    model_id: ModelID
    provider_id: ProviderID
    display_name: str
    capabilities: List[ProviderCapability] = field(default_factory=list)
    context_length: int = 8192
    metadata: ModelMetadata = field(default_factory=dict)


@dataclass
class ProviderRequest:
    """Request to a provider."""

    request_id: RequestID
    provider_id: ProviderID
    model_id: ModelID
    input: Union[str, List[Dict[str, str]]]
    parameters: RequestParameters = field(default_factory=dict)
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Response from a provider."""

    request_id: RequestID
    provider_id: ProviderID
    model_id: ModelID
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    usage: UsageMetrics = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """State of a provider session."""

    session_id: SessionID
    provider_id: ProviderID
    model_id: ModelID
    context: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingRule:
    """Rule for routing requests to providers."""

    task: str
    provider_id: Optional[ProviderID]
    model_id: Optional[ModelID]
    policy: RoutingPolicy
    priority: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuration for retrying failed requests."""

    policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = 0.1


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    max_requests: int = 100
    window_seconds: float = 60.0
    tokens: int = 100
    refill_rate: float = 1.0


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""

    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    max_failures: int = 3
    endpoint: str = "/health"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking."""

    iterations: int = 5
    warmup_iterations: int = 2
    input_size: int = 1000
    max_tokens: int = 100


# --- Protocols ---
@runtime_checkable
class ProviderPlugin(Protocol):
    """Protocol for provider plugins."""

    provider_id: ProviderID
    display_name: str
    provider_type: ProviderType
    capabilities: Dict[ProviderCapability, bool]

    def initialize(self, settings: ProviderSettings) -> None:
        """Initialize the provider plugin."""
        ...

    def send(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider."""
        ...

    async def send_async(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request to the provider asynchronously."""
        ...

    def supports(self, capability: ProviderCapability) -> bool:
        """Check if the provider supports a capability."""
        ...

    def health_check(self) -> HealthMetrics:
        """Perform a health check."""
        ...


@runtime_checkable
class KeyStorageBackend(Protocol):
    """Protocol for secure key storage backends."""

    def save(self, provider_id: ProviderID, key: APIKey) -> None:
        """Save an API key."""
        ...

    def load(self, provider_id: ProviderID) -> Optional[APIKey]:
        """Load an API key."""
        ...

    def delete(self, provider_id: ProviderID) -> None:
        """Delete an API key."""
        ...

    def list_keys(self) -> List[ProviderID]:
        """List all stored provider IDs."""
        ...


@runtime_checkable
class HealthMonitor(Protocol):
    """Protocol for health monitoring."""

    def check(self, provider_id: ProviderID) -> HealthMetrics:
        """Perform a health check."""
        ...

    def monitor(self, provider_id: ProviderID) -> None:
        """Start monitoring a provider."""
        ...

    def stop_monitoring(self, provider_id: ProviderID) -> None:
        """Stop monitoring a provider."""
        ...


@runtime_checkable
class LoadBalancer(Protocol):
    """Protocol for load balancing."""

    def select_provider(
        self, providers: List[ProviderID], policy: Optional[RoutingPolicy] = None
    ) -> Optional[ProviderID]:
        """Select a provider based on the policy."""
        ...

    def record_request(self, provider_id: ProviderID) -> None:
        """Record a request to a provider."""
        ...


@runtime_checkable
class FailoverManager(Protocol):
    """Protocol for failover management."""

    def get_fallback(self, provider_id: ProviderID) -> Optional[ProviderID]:
        """Get a fallback provider."""
        ...

    def record_failure(self, provider_id: ProviderID) -> None:
        """Record a failure for a provider."""
        ...

    def reset(self, provider_id: ProviderID) -> None:
        """Reset the failure count for a provider."""
        ...
