"""Integration layer for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import (
        HealthMetrics,
        ProviderCapability,
        ProviderID,
        ProviderRequest,
        ProviderResponse,
        ProviderSettings,
        RequestID,
    )

from .constants import ProviderCapability
from .exceptions import MaxRetriesExceededError, RequestFailedError, RequestTimeoutError
from .interfaces import ProviderAdapter
from .types import RetryConfig


try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class RetryState:
    """State for retry logic."""

    attempt: int = 0
    last_error: Optional[str] = None
    last_delay: float = 0.0


class RetryManager:
    """Manages retry logic for provider requests."""

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        self._config = config or RetryConfig()
        self._lock = RLock()

    def should_retry(self, state: RetryState) -> bool:
        """Check if a request should be retried."""
        return state.attempt < self._config.max_retries

    def get_delay(self, state: RetryState) -> float:
        """Get the delay before the next retry."""
        if self._config.policy == "fixed":
            return self._config.base_delay
        elif self._config.policy == "linear":
            return self._config.base_delay * (state.attempt + 1)
        elif self._config.policy == "exponential":
            return min(
                self._config.base_delay * (2 ** state.attempt),
                self._config.max_delay,
            )
        else:
            return self._config.base_delay

    def apply_jitter(self, delay: float) -> float:
        """Apply jitter to the delay."""
        import random
        jitter = delay * self._config.jitter
        return delay + random.uniform(-jitter, jitter)


class RateLimiter:
    """Rate limiter for provider requests."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._tokens: Dict[str, List[float]] = {}
        self._lock = RLock()

    def is_allowed(self, provider_id: str) -> bool:
        """Check if a request is allowed."""
        with self._lock:
            now = time.time()
            if provider_id not in self._tokens:
                self._tokens[provider_id] = []
            self._tokens[provider_id] = [
                t for t in self._tokens[provider_id] if now - t < self._window_seconds
            ]
            return len(self._tokens[provider_id]) < self._max_requests

    def record_request(self, provider_id: str) -> None:
        """Record a request."""
        with self._lock:
            if provider_id not in self._tokens:
                self._tokens[provider_id] = []
            self._tokens[provider_id].append(time.time())


@dataclass
class ProviderRequest:
    """Request to a provider."""

    request_id: RequestID
    provider_id: str
    model: str
    input: Any
    parameters: Dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    image: bool = False
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Response from a provider."""

    request_id: RequestID
    provider_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HTTPProviderAdapter(ProviderAdapter):
    """
    HTTP-based provider adapter with:
    - Retry logic
    - Rate limiting
    - Streaming support
    - Error handling
    """

    def __init__(
        self,
        provider_id: str,
        configuration: Optional[Dict[str, Any]] = None,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.provider_id = provider_id
        self.configuration = configuration or {}
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._lock = RLock()
        self._retry_manager = RetryManager(
            RetryConfig(
                policy="exponential",
                max_retries=max_retries,
                base_delay=1.0,
                max_delay=30.0,
                jitter=0.1,
            )
        )
        self._rate_limiter = RateLimiter(max_requests=100, window_seconds=60.0)

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Get the provider's capabilities."""
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
        }

    def initialize(self, settings: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider adapter."""
        if settings:
            self.configuration.update(settings)

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the provider."""
        normalized = self._normalize_request(request)
        try:
            if not self._rate_limiter.is_allowed(self.provider_id):
                return self._error_response(normalized, "Rate limit exceeded")

            if normalized["stream"]:
                response = self._send_streaming(normalized)
            else:
                response = self._send_request(normalized)

            self._rate_limiter.record_request(self.provider_id)
            return self._normalize_response(normalized, response)
        except Exception as e:
            return self._error_response(normalized, str(e))

    async def send_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the provider asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, request)

    def supports(self, capability: ProviderCapability) -> bool:
        """Check if the provider supports a capability."""
        return self.capabilities.get(capability, False)

    def health_check(self) -> HealthMetrics:
        """Perform a health check."""
        try:
            if httpx is None:
                return HealthMetrics(
                    latency_ms=0.0,
                    error_rate=1.0,
                    availability=0.0,
                    last_check_time=time.time(),
                )
            start_time = time.time()
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(f"{self.base_url}/health")
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

    def _normalize_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a request."""
        return {
            "request_id": request.get("request_id", ""),
            "provider_id": self.provider_id,
            "model": request.get("model", self.configuration.get("default_model", "")),
            "input": request.get("input", request.get("prompt", "")),
            "parameters": request.get("parameters", {}),
            "stream": bool(request.get("stream", False)),
            "image": bool(request.get("image", False)),
            "tool_calls": request.get("tool_calls", []),
            "metadata": request.get("metadata", {}),
        }

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a synchronous request."""
        if httpx is None:
            raise RequestFailedError("httpx is not installed")

        url, payload = self._build_payload(request)
        headers = self._build_headers()
        timeout = httpx.Timeout(self.timeout_seconds)

        state = RetryState()
        while self._retry_manager.should_retry(state):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as e:
                state.attempt += 1
                state.last_error = str(e)
                delay = self._retry_manager.get_delay(state)
                time.sleep(delay)
            except httpx.HTTPStatusError as e:
                state.attempt += 1
                state.last_error = e.response.text
                delay = self._retry_manager.get_delay(state)
                time.sleep(delay)

        raise MaxRetriesExceededError(f"Max retries exceeded: {state.last_error}")

    def _send_streaming(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a streaming request."""
        if httpx is None:
            raise RequestFailedError("httpx is not installed")

        url, payload = self._build_payload(request)
        headers = self._build_headers()
        timeout = httpx.Timeout(self.timeout_seconds)
        chunks: List[Dict[str, Any]] = []

        state = RetryState()
        while self._retry_manager.should_retry(state):
            try:
                with httpx.Client(timeout=timeout) as client:
                    with client.stream("POST", url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        for chunk in response.iter_text():
                            try:
                                parsed = json.loads(chunk)
                            except ValueError:
                                parsed = {"chunk": chunk}
                            chunks.append(parsed)
                return {"stream": chunks, "status_code": response.status_code}
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                state.attempt += 1
                state.last_error = str(e)
                delay = self._retry_manager.get_delay(state)
                time.sleep(delay)

        raise MaxRetriesExceededError(f"Max retries exceeded: {state.last_error}")

    def _build_headers(self) -> Dict[str, str]:
        """Build headers for the request."""
        headers = {"Content-Type": "application/json", **self.headers}
        return headers

    def _build_payload(self, request: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Build the payload for the request."""
        raise NotImplementedError("Subclasses must implement _build_payload")

    def _normalize_response(
        self, request: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize the response."""
        output: Dict[str, Any] = {}
        usage: Dict[str, Any] = {}

        if "stream" in response:
            output["stream"] = response["stream"]
        elif isinstance(response, dict):
            output["raw"] = response
            output["text"] = self._extract_text(response)
            output["images"] = self._extract_images(response)
            output["tool_calls"] = self._extract_tool_calls(response)
            usage = self._extract_usage(response)

        return {
            "request_id": request["request_id"],
            "provider_id": self.provider_id,
            "success": True,
            "output": output,
            "metadata": {"model": request["model"], "provider": self.provider_id},
            "error": None,
            "usage": usage,
        }

    def _extract_text(self, response: Dict[str, Any]) -> str:
        """Extract text from the response."""
        if "choices" in response:
            texts: List[str] = []
            for choice in response["choices"]:
                if isinstance(choice, dict):
                    texts.append(
                        str(
                            choice.get("text", choice.get("message", {}).get("content", ""))
                        )
                    )
            return "\n".join(filter(None, texts))
        if "output" in response and isinstance(response["output"], list):
            text_values = [str(item) for item in response["output"]]
            return "\n".join(text_values)
        return str(response.get("text", ""))

    def _extract_images(self, response: Dict[str, Any]) -> List[str]:
        """Extract images from the response."""
        if "data" in response and isinstance(response["data"], list):
            urls = []
            for item in response["data"]:
                if isinstance(item, dict):
                    if "url" in item:
                        urls.append(str(item["url"]))
                    elif "b64_json" in item:
                        urls.append(str(item["b64_json"]))
            return urls
        return []

    def _extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from the response."""
        if "tool_calls" in response:
            return response["tool_calls"]
        if "choices" in response:
            calls: List[Dict[str, Any]] = []
            for choice in response["choices"]:
                if isinstance(choice, dict) and choice.get("tool"):
                    calls.append(choice["tool"])
            return calls
        return []

    def _extract_usage(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract usage from the response."""
        usage = response.get("usage")
        if isinstance(usage, dict):
            return dict(usage)
        return {}

    def _error_response(
        self, request: Dict[str, Any], error_message: str
    ) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "request_id": request["request_id"],
            "provider_id": self.provider_id,
            "success": False,
            "output": {},
            "metadata": {"model": request["model"], "provider": self.provider_id},
            "error": error_message,
        }


class ProviderCapabilityManager:
    """Manages capabilities for providers."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, Dict[ProviderCapability, bool]] = {}
        self._lock = RLock()

    def register(
        self, provider_id: str, capabilities: Dict[ProviderCapability, bool]
    ) -> None:
        """Register capabilities for a provider."""
        with self._lock:
            self._capabilities[provider_id] = capabilities

    def get_capabilities(self, provider_id: str) -> Dict[ProviderCapability, bool]:
        """Get capabilities for a provider."""
        return self._capabilities.get(provider_id, {})

    def has_capability(
        self, provider_id: str, capability: ProviderCapability
    ) -> bool:
        """Check if a provider has a capability."""
        return self.get_capabilities(provider_id).get(capability, False)


class ProviderAuthenticationManager:
    """Manages authentication for providers."""

    def __init__(self) -> None:
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def configure(self, provider_id: str, credentials: Dict[str, Any]) -> None:
        """Configure credentials for a provider."""
        with self._lock:
            self._credentials[provider_id] = dict(credentials)

    def get_credentials(self, provider_id: str) -> Dict[str, Any]:
        """Get credentials for a provider."""
        return self._credentials.get(provider_id, {})


class ProviderConfigurationLoader:
    """Loads configurations for providers."""

    def __init__(self) -> None:
        self._configurations: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def load(self, provider_id: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Load a configuration for a provider."""
        with self._lock:
            self._configurations[provider_id] = configuration
            return configuration

    def get_configuration(self, provider_id: str) -> Dict[str, Any]:
        """Get the configuration for a provider."""
        return self._configurations.get(provider_id, {})


class ProviderSessionManager:
    """Manages sessions for providers."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def start_session(
        self, provider_id: str, model_id: Optional[str] = None
    ) -> str:
        """Start a new session."""
        import uuid

        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = {
                "provider_id": provider_id,
                "model_id": model_id,
                "context": [],
                "metadata": {},
            }
        return session_id

    def end_session(self, session_id: str) -> None:
        """End a session."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get a session."""
        return self._sessions.get(session_id, {})


class ProviderConnectionManager:
    """Manages connections for providers."""

    def __init__(self) -> None:
        self._connections: Dict[str, bool] = {}
        self._lock = RLock()

    def connect(self, provider_id: str) -> bool:
        """Connect to a provider."""
        with self._lock:
            self._connections[provider_id] = True
            return True

    def disconnect(self, provider_id: str) -> None:
        """Disconnect from a provider."""
        with self._lock:
            self._connections.pop(provider_id, None)

    def is_connected(self, provider_id: str) -> bool:
        """Check if a provider is connected."""
        return self._connections.get(provider_id, False)


class ProviderRateLimitManager:
    """Manages rate limits for providers."""

    def __init__(self) -> None:
        self._limits: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def configure(self, provider_id: str, limit: Dict[str, Any]) -> None:
        """Configure rate limits for a provider."""
        with self._lock:
            self._limits[provider_id] = dict(limit)

    def is_allowed(self, provider_id: str) -> bool:
        """Check if a request is allowed."""
        limit = self._limits.get(provider_id, {})
        if not limit:
            return True
        return True  # Placeholder for actual rate limiting logic


class ProviderUsageManager:
    """Manages usage tracking for providers."""

    def __init__(self) -> None:
        self._usage: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def record_usage(
        self,
        provider_id: str,
        requests: int = 1,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record usage for a provider."""
        with self._lock:
            if provider_id not in self._usage:
                self._usage[provider_id] = {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }
            self._usage[provider_id]["total_requests"] += requests
            self._usage[provider_id]["total_tokens"] += tokens
            self._usage[provider_id]["total_cost"] += cost

    def get_usage(self, provider_id: str) -> Dict[str, Any]:
        """Get usage for a provider."""
        return self._usage.get(provider_id, {})


class ProviderStreamingManager:
    """Manages streaming for providers."""

    def __init__(self) -> None:
        self._streams: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

    def register_stream(
        self, stream_id: str, chunks: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Register a stream."""
        with self._lock:
            self._streams[stream_id] = list(chunks or [])

    def get_stream(self, stream_id: str) -> List[Dict[str, Any]]:
        """Get a stream."""
        return self._streams.get(stream_id, [])


class ProviderRetryManager:
    """Manages retry logic for providers."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self._lock = RLock()

    def should_retry(self, attempt: int) -> bool:
        """Check if a request should be retried."""
        return attempt < self.max_retries


class CapabilityMatcher:
    """Matches providers by capability."""

    def matches(
        self, requirements: Dict[ProviderCapability, bool], capabilities: Dict[ProviderCapability, bool]
    ) -> bool:
        """Check if capabilities match requirements."""
        return all(
            capabilities.get(key, False) for key, required in requirements.items() if required
        )


class ProviderSelector:
    """Selects providers based on requirements."""

    def __init__(self) -> None:
        self._lock = RLock()

    def select(
        self,
        providers: List[str],
        requirements: Dict[ProviderCapability, bool],
        capabilities: Dict[str, Dict[ProviderCapability, bool]],
    ) -> List[str]:
        """Select providers that match the requirements."""
        return [
            provider
            for provider in providers
            if self._matches(requirements, capabilities.get(provider, {}))
        ]

    def _matches(
        self, requirements: Dict[ProviderCapability, bool], capabilities: Dict[ProviderCapability, bool]
    ) -> bool:
        """Check if capabilities match requirements."""
        return all(
            capabilities.get(key, False) for key, required in requirements.items() if required
        )


class ProviderRouter:
    """Routes requests to providers."""

    def __init__(self, provider_manager: Optional[Any] = None) -> None:
        self._provider_manager = provider_manager
        self._lock = RLock()

    def select_provider(
        self,
        requirements: Dict[ProviderCapability, bool],
        policy: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Select a provider based on requirements and policy."""
        if self._provider_manager is None:
            return None
        providers = list(self._provider_manager.list_providers())
        if not providers:
            return None
        return providers[0]


class FallbackManager:
    """Manages fallback providers."""

    def __init__(self) -> None:
        self._history: List[str] = []
        self._lock = RLock()

    def record(self, provider_id: str) -> None:
        """Record a fallback."""
        with self._lock:
            self._history.append(provider_id)

    def get_history(self) -> List[str]:
        """Get fallback history."""
        return list(self._history)


class LoadDistributionManager:
    """Manages load distribution."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._lock = RLock()

    def next_provider(self, providers: List[str]) -> Optional[str]:
        """Get the next provider using round-robin."""
        if not providers:
            return None
        with self._lock:
            for provider in providers:
                self._counters[provider] = self._counters.get(provider, 0) + 1
            min_provider = min(providers, key=lambda p: self._counters.get(p, 0))
            return min_provider


class CostAwareRouter(ProviderRouter):
    """Routes requests based on cost."""

    pass


class LatencyAwareRouter(ProviderRouter):
    """Routes requests based on latency."""

    pass


class HealthAwareRouter(ProviderRouter):
    """Routes requests based on health."""

    pass


class ModelCatalogManager:
    """Manages the model catalog."""

    def __init__(self) -> None:
        self._models: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def register_model(
        self,
        model_id: str,
        provider: str,
        capabilities: Optional[List[str]] = None,
        context_length: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a model."""
        with self._lock:
            record = {
                "model_id": model_id,
                "provider": provider,
                "capabilities": capabilities or [],
                "context_length": context_length or 8192,
                "metadata": metadata or {},
            }
            self._models[model_id] = record
            return record

    def resolve_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Resolve a model by ID."""
        return self._models.get(model_id)


# --- New Classes for Phase 8 ---


class ParallelRequestManager:
    """Manages parallel execution of requests to multiple providers."""

    def __init__(self, hub: Any = None, max_concurrency: int = 5) -> None:
        self._hub = hub
        self.max_concurrency = max_concurrency
        self._lock = RLock()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_parallel(
        self, provider_ids: List[str], request: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute requests to multiple providers in parallel."""
        if not provider_ids:
            return []
        tasks = []
        for provider_id in provider_ids:
            tasks.append(self._execute_single(provider_id, request))
        return await asyncio.gather(*tasks)

    async def _execute_single(
        self, provider_id: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single request to a provider."""
        async with self._semaphore:
            if self._hub is None:
                return {"error": "Hub is required for parallel execution"}
            adapter = self._hub.get_adapter(provider_id)
            if adapter is None:
                return {"error": f"No adapter for provider {provider_id}"}
            try:
                response = await adapter.send_async(request)
                return {"provider_id": provider_id, "response": response}
            except Exception as e:
                return {"provider_id": provider_id, "error": str(e)}


class ResponseAggregator:
    """Aggregates responses from multiple providers."""

    def __init__(self) -> None:
        self._lock = RLock()

    def aggregate(
        self, responses: List[Dict[str, Any]], method: str = "majority"
    ) -> Dict[str, Any]:
        """Aggregate responses using the specified method."""
        if not responses:
            return {"error": "No responses to aggregate"}
        if method == "majority":
            return self._majority_vote(responses)
        elif method == "concatenate":
            return self._concatenate(responses)
        elif method == "average":
            return self._average(responses)
        else:
            return self._majority_vote(responses)

    def _majority_vote(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate responses using majority vote."""
        texts = [
            r.get("response", {}).get("output", {}).get("text", "")
            for r in responses
            if r.get("response", {}).get("success", False)
        ]
        if not texts:
            return {"error": "No successful responses"}
        from collections import Counter
        most_common = Counter(texts).most_common(1)[0][0]
        return {
            "aggregated": most_common,
            "method": "majority_vote",
            "responses": responses,
        }

    def _concatenate(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate responses by concatenation."""
        texts = [
            r.get("response", {}).get("output", {}).get("text", "")
            for r in responses
            if r.get("response", {}).get("success", False)
        ]
        if not texts:
            return {"error": "No successful responses"}
        combined = "\n\n".join(texts)
        return {
            "aggregated": combined,
            "method": "concatenation",
            "responses": responses,
        }

    def _average(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate responses by averaging (for numerical outputs)."""
        # Placeholder for numerical aggregation
        return {"error": "Numerical aggregation not implemented"}


class StreamingAggregator:
    """Aggregates streaming responses from multiple providers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._streams: Dict[str, List[Dict[str, Any]]] = {}

    def aggregate_streams(
        self, streams: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Aggregate streaming chunks from multiple providers."""
        aggregated = []
        for provider_id, chunks in streams.items():
            for chunk in chunks:
                aggregated.append({"provider_id": provider_id, "chunk": chunk})
        return aggregated
