from __future__ import annotations

import json
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional


class _FallbackHttpxModule:
    class Timeout:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

    class RequestError(Exception):
        pass

    class HTTPStatusError(Exception):
        def __init__(self, response: Any | None = None, *args: Any) -> None:
            self.response = response
            super().__init__(*args)

    class Client:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._args = args
            self._kwargs = kwargs

        def __enter__(self) -> "_FallbackHttpxModule.Client":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
            return False

        def post(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("httpx is not installed")

        def stream(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("httpx is not installed")


try:
    import httpx
except ImportError:  # pragma: no cover - exercised in minimal environments
    httpx = _FallbackHttpxModule()

from ..model_runtime.models import ModelConfiguration, ModelMetadata, ModelUsage


@dataclass(frozen=True)
class ProviderRequest:
    request_id: str
    provider_id: str
    model: str
    input: str | list[dict[str, str]] = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    stream: bool = False
    image: bool = False
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    request_id: str
    provider_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCatalogEntry:
    model_id: str
    provider: str
    capabilities: List[str] = field(default_factory=list)
    context_length: int | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProviderAdapter:
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        self.provider_id = provider_id
        self.configuration = configuration or {}
        self._lock = RLock()

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"provider_id": self.provider_id, "request": request}

    def supports(self, capability: str) -> bool:
        return False


class HTTPProviderAdapter(BaseProviderAdapter):
    def __init__(
        self,
        provider_id: str,
        configuration: dict[str, Any] | None = None,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        super().__init__(provider_id, configuration)
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_request(request)
        try:
            if normalized["stream"]:
                response = self._send_streaming(normalized)
            else:
                response = self._send_request(normalized)
            return self._normalize_response(normalized, response)
        except Exception as exc:
            return self._error_response(normalized, str(exc))

    def supports(self, capability: str) -> bool:
        return bool(self.configuration.get("capabilities", {}).get(capability, False))

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
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

    def _send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        if httpx is None:
            return {"status_code": 0, "error": "httpx is not installed"}
        url, payload = self._build_payload(request)
        headers = self._build_headers()
        timeout = httpx.Timeout(self.timeout_seconds)

        last_error: str | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as exc:
                last_error = str(exc)
                if attempt == self.max_retries:
                    raise
            except httpx.HTTPStatusError as exc:
                last_error = exc.response.text
                if attempt == self.max_retries:
                    raise
        raise RuntimeError(last_error or "provider request failed")

    def _send_streaming(self, request: dict[str, Any]) -> dict[str, Any]:
        if httpx is None:
            return {"stream": [], "status_code": 0, "error": "httpx is not installed"}
        url, payload = self._build_payload(request)
        headers = self._build_headers()
        timeout = httpx.Timeout(self.timeout_seconds)
        chunks: list[dict[str, Any]] = []

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

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.headers}
        return headers

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError

    def _normalize_response(self, request: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        usage: dict[str, Any] = {}
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

    def _extract_text(self, response: dict[str, Any]) -> str:
        if "choices" in response:
            texts: list[str] = []
            for choice in response["choices"]:
                if isinstance(choice, dict):
                    texts.append(str(choice.get("text", choice.get("message", {}).get("content", ""))))
            return "\n".join(filter(None, texts))
        if "output" in response and isinstance(response["output"], list):
            text_values = [str(item) for item in response["output"]]
            return "\n".join(text_values)
        return str(response.get("text", ""))

    def _extract_images(self, response: dict[str, Any]) -> list[str]:
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

    def _extract_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        if "tool_calls" in response:
            return response["tool_calls"]
        if "choices" in response:
            calls: list[dict[str, Any]] = []
            for choice in response["choices"]:
                if isinstance(choice, dict) and choice.get("tool"):
                    calls.append(choice["tool"])
            return calls
        return []

    def _extract_usage(self, response: dict[str, Any]) -> dict[str, Any]:
        usage = response.get("usage")
        if isinstance(usage, dict):
            return dict(usage)
        return {}

    def _error_response(self, request: dict[str, Any], error_message: str) -> dict[str, Any]:
        return {
            "request_id": request["request_id"],
            "provider_id": self.provider_id,
            "success": False,
            "output": {},
            "metadata": {"model": request["model"], "provider": self.provider_id},
            "error": error_message,
        }


class ProviderCapabilityManager:
    def __init__(self) -> None:
        self._capabilities: Dict[str, Dict[str, bool]] = {}
        self._lock = RLock()

    def register(self, provider_id: str, capabilities: dict[str, bool]) -> None:
        with self._lock:
            self._capabilities[provider_id] = capabilities

    def get_capabilities(self, provider_id: str) -> Dict[str, bool]:
        with self._lock:
            return dict(self._capabilities.get(provider_id, {}))


class ProviderAuthenticationManager:
    def __init__(self) -> None:
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def configure(self, provider_id: str, credentials: dict[str, Any]) -> None:
        with self._lock:
            self._credentials[provider_id] = dict(credentials)

    def get_credentials(self, provider_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._credentials.get(provider_id, {}))


class ProviderConfigurationLoader:
    def __init__(self) -> None:
        self._configurations: Dict[str, ModelConfiguration] = {}
        self._lock = RLock()

    def load(self, provider_id: str, configuration: ModelConfiguration) -> ModelConfiguration:
        with self._lock:
            self._configurations[provider_id] = configuration
            return configuration


class ProviderSessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def start_session(self, provider_id: str, model_id: str | None = None) -> str:
        with self._lock:
            session_id = f"{provider_id}:{model_id or 'default'}"
            self._sessions[session_id] = {"provider_id": provider_id, "model_id": model_id}
            return session_id

    def end_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


class ProviderConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[str, bool] = {}
        self._lock = RLock()

    def connect(self, provider_id: str) -> bool:
        with self._lock:
            self._connections[provider_id] = True
            return True

    def disconnect(self, provider_id: str) -> None:
        with self._lock:
            self._connections.pop(provider_id, None)


class ProviderRateLimitManager:
    def __init__(self) -> None:
        self._limits: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def configure(self, provider_id: str, limit: dict[str, Any]) -> None:
        with self._lock:
            self._limits[provider_id] = dict(limit)


class ProviderUsageManager:
    def __init__(self) -> None:
        self._usage: Dict[str, ModelUsage] = {}
        self._lock = RLock()

    def record_usage(self, provider_id: str, requests: int, tokens: int, cost: float, details: Optional[dict[str, Any]] = None) -> ModelUsage:
        with self._lock:
            previous = self._usage.get(provider_id, ModelUsage(model_id=provider_id))
            usage = ModelUsage(
                model_id=provider_id,
                total_requests=previous.total_requests + requests,
                total_tokens=previous.total_tokens + tokens,
                total_cost=previous.total_cost + cost,
                details={**previous.details, **(details or {})},
            )
            self._usage[provider_id] = usage
            return usage

    def get_usage(self, provider_id: str) -> ModelUsage:
        with self._lock:
            return self._usage.get(provider_id, ModelUsage(model_id=provider_id))


class ProviderStreamingManager:
    def __init__(self) -> None:
        self._streams: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

    def register_stream(self, stream_id: str, chunks: list[dict[str, Any]] | None = None) -> None:
        with self._lock:
            self._streams[stream_id] = list(chunks or [])

    def get_stream(self, stream_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._streams.get(stream_id, []))


class ProviderRetryManager:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self._lock = RLock()

    def should_retry(self, attempt: int) -> bool:
        with self._lock:
            return attempt < self.max_retries


class CapabilityMatcher:
    def matches(self, requirements: dict[str, bool], capabilities: dict[str, bool]) -> bool:
        return all(capabilities.get(key, False) for key, required in requirements.items() if required)


class ProviderSelector:
    def __init__(self) -> None:
        self._lock = RLock()

    def select(self, providers: list[str], requirements: dict[str, bool], capabilities: dict[str, Dict[str, bool]]) -> list[str]:
        return [provider for provider in providers if self._matches(requirements, capabilities.get(provider, {}))]

    def _matches(self, requirements: dict[str, bool], capabilities: dict[str, bool]) -> bool:
        return all(capabilities.get(key, False) for key, required in requirements.items() if required)


class ProviderRouter:
    def __init__(self, provider_manager: Any | None = None) -> None:
        self._provider_manager = provider_manager
        self._lock = RLock()

    def select_provider(self, requirements: dict[str, bool], policy: dict[str, Any] | None = None) -> str | None:
        providers = []
        if self._provider_manager is not None:
            providers = list(self._provider_manager._providers.keys())
        if not providers:
            return None
        return providers[0]


class FallbackManager:
    def __init__(self) -> None:
        self._history: List[str] = []
        self._lock = RLock()

    def record(self, provider_id: str) -> None:
        with self._lock:
            self._history.append(provider_id)

    def get_history(self) -> List[str]:
        with self._lock:
            return list(self._history)


class LoadDistributionManager:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._lock = RLock()

    def next_provider(self, providers: list[str]) -> str | None:
        if not providers:
            return None
        return providers[0]


class CostAwareRouter(ProviderRouter):
    pass


class LatencyAwareRouter(ProviderRouter):
    pass


class HealthAwareRouter(ProviderRouter):
    pass


class ModelCatalogManager:
    def __init__(self) -> None:
        self._models: Dict[str, ModelCatalogEntry] = {}
        self._lock = RLock()

    def register_model(self, model_id: str, provider: str, capabilities: list[str] | None = None, context_length: int | None = None, metadata: dict[str, Any] | None = None) -> ModelCatalogEntry:
        with self._lock:
            record = ModelCatalogEntry(
                model_id=model_id,
                provider=provider,
                capabilities=capabilities or [],
                context_length=context_length,
                metadata=metadata or {},
            )
            self._models[model_id] = record
            return record

    def resolve_model(self, model_id: str) -> ModelCatalogEntry:
        with self._lock:
            return self._models[model_id]

    def resolve_model(self, model_id: str) -> ModelCatalogEntry | None:
        with self._lock:
            return self._models.get(model_id)
