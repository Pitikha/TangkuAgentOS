"""Constants for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from enum import Enum


# --- Provider Constants ---
DEFAULT_PROVIDER_TIMEOUT = 30.0  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_URL = ""
DEFAULT_PROVIDER_TYPE = "cloud"


# --- Model Constants ---
DEFAULT_MODEL_CONTEXT_LENGTH = 8192
DEFAULT_MODEL_FAMILY = "generic"
DEFAULT_MODEL_SPEED = "medium"
DEFAULT_MODEL_QUALITY = "standard"


# --- Rate Limit Constants ---
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60.0  # seconds
DEFAULT_RATE_LIMIT_TOKENS = 100
DEFAULT_RATE_LIMIT_REFILL_RATE = 1.0


# --- Retry Constants ---
DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds
DEFAULT_RETRY_MAX_DELAY = 30.0  # seconds
DEFAULT_RETRY_JITTER = 0.1


# --- Health Check Constants ---
DEFAULT_HEALTH_CHECK_INTERVAL = 30.0  # seconds
DEFAULT_HEALTH_CHECK_TIMEOUT = 5.0  # seconds
DEFAULT_HEALTH_CHECK_MAX_FAILURES = 3
DEFAULT_HEALTH_CHECK_ENDPOINT = "/health"


# --- Benchmark Constants ---
DEFAULT_BENCHMARK_ITERATIONS = 5
DEFAULT_BENCHMARK_WARMUP_ITERATIONS = 2
DEFAULT_BENCHMARK_INPUT_SIZE = 1000
DEFAULT_BENCHMARK_MAX_TOKENS = 100


# --- Storage Constants ---
DEFAULT_STORAGE_PATH = "/tmp/tangku-provider-runtime"
DEFAULT_KEY_STORAGE_PATH = "/tmp/tangku-provider-keys.json"
DEFAULT_STATE_STORAGE_PATH = "/tmp/tangku-provider-state.json"


# --- Provider IDs ---
class ProviderID(Enum):
    """Supported provider IDs."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    COHERE = "cohere"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    AZURE_OPENAI = "azure_openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    LLAMACPP = "llamacpp"
    VLLM = "vllm"
    LOCAL = "local"
    CUSTOM = "custom"


# --- Provider Types ---
class ProviderType(Enum):
    """Types of AI providers."""

    CLOUD = "cloud"
    LOCAL = "local"
    CUSTOM = "custom"
    PLUGIN = "plugin"


# --- Provider Statuses ---
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


# --- Provider Capabilities ---
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


# --- Routing Policies ---
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


# --- Load Balancing Strategies ---
class LoadBalancingStrategy(Enum):
    """Strategies for load balancing."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"


# --- Retry Policies ---
class RetryPolicy(Enum):
    """Policies for retrying failed requests."""

    NONE = "none"
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    JITTER = "jitter"


# --- Rate Limit Strategies ---
class RateLimitStrategy(Enum):
    """Strategies for rate limiting."""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


# --- Health Check Statuses ---
class HealthCheckStatus(Enum):
    """Status of a health check."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    TIMEOUT = "timeout"


# --- Task Types ---
class TaskType(Enum):
    """Types of tasks for routing."""

    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    IMAGE_GENERATION = "image_generation"
    TOOL_CALLING = "tool_calling"
    FUNCTION_CALLING = "function_calling"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    QUESTION_ANSWERING = "question_answering"


# --- Environment Variables ---
TANGKU_PROVIDER_KEY_PREFIX = "TANGKU_PROVIDER_"
TANGKU_PROVIDER_KEY_SUFFIX = "_KEY"
TANGKU_PROVIDER_DEFAULT_KEY = "TANGKU_PROVIDER_KEY"
