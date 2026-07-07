from __future__ import annotations

import copy
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - exercised in minimal environments
    httpx = None

from ..core_runtime.event_bus import EventBus
from ..kernel_runtime.kernel import KernelManager
from ..model_runtime.models import ModelConfiguration
from .manager import ProviderManager


@dataclass(frozen=True)
class ProviderDefinition:
    provider_id: str
    display_name: str
    provider_type: str = "cloud"
    capabilities: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderHub:
    """Unified provider hub that extends the existing provider runtime."""

    def __init__(self, provider_manager: ProviderManager | None = None, kernel: KernelManager | None = None, event_bus: EventBus | None = None, state_path: str | None = None) -> None:
        self._provider_manager = provider_manager or ProviderManager()
        self._kernel = kernel
        self._event_bus = event_bus or getattr(self._kernel, "_event_bus", None) or EventBus()
        self._state_path = Path(state_path or "/tmp/tangku-provider-hub.json")
        self._definitions: dict[str, ProviderDefinition] = {}
        self._models: dict[str, dict[str, Any]] = {}
        self._provider_states: dict[str, dict[str, Any]] = {}
        self._routing_rules: list[dict[str, Any]] = []
        self._benchmark_history: list[dict[str, Any]] = []
        self._lock = RLock()
        self._register_builtin_definitions()
        self.load_state(self._state_path)
        self._emit("provider.hub.ready", {"provider_count": len(self.list_providers())})

    def _emit(self, event_name: str, payload: dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload, metadata={"source": "provider-hub"})
        except Exception:
            return None

    def _register_builtin_definitions(self) -> None:
        for provider_id, definition in {
            "openai": ProviderDefinition("openai", "OpenAI", "cloud", {"chat": True, "streaming": True, "function_calling": True}),
            "anthropic": ProviderDefinition("anthropic", "Anthropic", "cloud", {"chat": True, "reasoning": True}),
            "google": ProviderDefinition("google", "Google Gemini", "cloud", {"chat": True, "vision": True}),
            "openrouter": ProviderDefinition("openrouter", "OpenRouter", "cloud", {"chat": True, "streaming": True}),
            "groq": ProviderDefinition("groq", "Groq", "cloud", {"chat": True, "streaming": True}),
            "deepseek": ProviderDefinition("deepseek", "DeepSeek", "cloud", {"chat": True, "reasoning": True}),
            "mistral": ProviderDefinition("mistral", "Mistral", "cloud", {"chat": True}),
            "cohere": ProviderDefinition("cohere", "Cohere", "cloud", {"chat": True, "embeddings": True}),
            "together": ProviderDefinition("together", "Together AI", "cloud", {"chat": True, "streaming": True}),
            "fireworks": ProviderDefinition("fireworks", "Fireworks AI", "cloud", {"chat": True}),
            "azure_openai": ProviderDefinition("azure_openai", "Azure OpenAI", "cloud", {"chat": True}),
            "ollama": ProviderDefinition("ollama", "Ollama", "local", {"chat": True, "offline": True, "streaming": True}),
            "lmstudio": ProviderDefinition("lmstudio", "LM Studio", "local", {"chat": True, "offline": True}),
            "llamacpp": ProviderDefinition("llamacpp", "llama.cpp", "local", {"chat": True, "offline": True}),
            "vllm": ProviderDefinition("vllm", "vLLM", "local", {"chat": True, "offline": True}),
        }.items():
            self._definitions[provider_id] = definition

    def register_provider(self, provider_id: str, settings: dict[str, Any] | None = None, capabilities: dict[str, bool] | None = None) -> dict[str, Any]:
        with self._lock:
            configuration = ModelConfiguration(provider_id=provider_id, settings=settings or {}, defaults={})
            self._provider_manager.add_provider(provider_id, configuration)
            definition = self._definitions.get(provider_id, ProviderDefinition(provider_id, provider_id))
            self._definitions[provider_id] = ProviderDefinition(
                provider_id=provider_id,
                display_name=definition.display_name,
                provider_type=definition.provider_type,
                capabilities={**definition.capabilities, **(capabilities or {})},
                metadata=definition.metadata,
            )
            self._provider_states[provider_id] = {"provider_id": provider_id, "status": "registered", "connected": False, "last_checked": None}
            self._emit("provider.registered", {"provider_id": provider_id, "capabilities": self._definitions[provider_id].capabilities})
            self.persist_state(self._state_path)
            return {"provider_id": provider_id, "capabilities": self._definitions[provider_id].capabilities}

    def list_providers(self) -> list[str]:
        with self._lock:
            return sorted(self._provider_manager._providers)

    def list_provider_details(self) -> list[dict[str, Any]]:
        with self._lock:
            providers: list[dict[str, Any]] = []
            for provider_id in sorted(self._provider_manager._providers):
                definition = self._definitions.get(provider_id, ProviderDefinition(provider_id, provider_id))
                state = self._provider_states.get(provider_id, {})
                providers.append({
                    "provider_id": provider_id,
                    "display_name": definition.display_name,
                    "provider_type": definition.provider_type,
                    "capabilities": dict(definition.capabilities),
                    "status": state.get("status", "registered"),
                    "connected": bool(state.get("connected", False)),
                    "last_checked": state.get("last_checked"),
                })
            return providers

    def detect_hardware(self) -> dict[str, Any]:
        with self._lock:
            hardware = {
                "platform": platform.platform(),
                "system": platform.system(),
                "python_version": platform.python_version(),
                "machine": platform.machine(),
                "cpu_count": os.cpu_count() or 1,
                "cpu_architecture": platform.machine(),
                "ram_gb": self._estimate_ram_gb(),
                "gpu": self._detect_gpu(),
                "cuda": False,
                "rocm": False,
                "metal": False,
            }
            try:
                hardware["cuda"] = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=False).returncode == 0
            except Exception:
                hardware["cuda"] = False
            if hardware["system"].lower() == "darwin":
                hardware["metal"] = True
            return hardware

    def _estimate_ram_gb(self) -> float:
        try:
            if sys.platform == "linux":
                with open("/proc/meminfo", "r", encoding="utf-8") as handle:
                    for line in handle:
                        if line.startswith("MemTotal"):
                            return round(int(line.split()[1]) / (1024 * 1024), 2)
        except Exception:
            return 0.0
        return 0.0

    def _detect_gpu(self) -> dict[str, Any]:
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,temperature.gpu,memory.total", "--format=csv,noheader"], capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                name, temperature, memory = result.stdout.strip().split(",")
                return {"name": name.strip(), "temperature_c": temperature.strip(), "memory": memory.strip()}
        except Exception:
            return {}
        return {}

    def detect_environment(self) -> dict[str, Any]:
        with self._lock:
            environment = {"hardware": self.detect_hardware(), "providers": self.list_provider_details()}
            self._provider_states["environment"] = environment
            self.persist_state(self._state_path)
            return environment

    def detect_local_providers(self, detectors: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            detected: list[dict[str, Any]] = []
            detectors = detectors or {}
            for provider_id, detector in detectors.items():
                try:
                    result = detector() if callable(detector) else detector
                except Exception:
                    continue
                if not isinstance(result, dict):
                    continue
                if result.get("available"):
                    self.register_provider(provider_id, {"base_url": result.get("base_url", "")}, capabilities={"offline": True, **self._capability_map(provider_id)})
                    self._provider_states[provider_id] = {
                        **self._provider_states.get(provider_id, {}),
                        "status": "detected",
                        "connected": True,
                        "last_checked": time.time(),
                        "details": result,
                    }
                    detected.append({"provider_id": provider_id, "available": True, "base_url": result.get("base_url", ""), "capabilities": self._definitions[provider_id].capabilities})
            return detected

    def detect_local_runtime(self, provider_id: str, base_url: str | None = None) -> dict[str, Any]:
        candidate_base_url = base_url or self._provider_base_url(provider_id)
        if not candidate_base_url:
            return {"provider_id": provider_id, "available": False}
        if httpx is None:
            return {"provider_id": provider_id, "available": False, "base_url": candidate_base_url, "health": {"status": "offline"}}
        endpoints = self._candidate_endpoints(provider_id, candidate_base_url)
        details: dict[str, Any] = {"provider_id": provider_id, "available": False, "base_url": candidate_base_url, "endpoints": []}
        for endpoint in endpoints:
            try:
                response = httpx.get(endpoint, timeout=1.5)
                if response.status_code < 400:
                    details["available"] = True
                    details["endpoints"].append({"url": endpoint, "status": response.status_code})
                    break
            except Exception:
                continue
        if details["available"]:
            details["capabilities"] = self._capability_map(provider_id)
            details["models"] = self._probe_models(provider_id, candidate_base_url)
            details["health"] = {"status": "healthy"}
        return details

    def _provider_base_url(self, provider_id: str) -> str | None:
        if provider_id == "ollama":
            return "http://127.0.0.1:11434"
        if provider_id == "lmstudio":
            return "http://127.0.0.1:1234"
        if provider_id == "llamacpp":
            return "http://127.0.0.1:8000"
        if provider_id == "vllm":
            return "http://127.0.0.1:8000"
        return None

    def _candidate_endpoints(self, provider_id: str, base_url: str) -> list[str]:
        if provider_id == "ollama":
            return [f"{base_url}/api/tags", f"{base_url}/health", f"{base_url}/api/version"]
        if provider_id == "lmstudio":
            return [f"{base_url}/v1/models", f"{base_url}/health", f"{base_url}/v1/models/list"]
        if provider_id == "llamacpp":
            return [f"{base_url}/health", f"{base_url}/v1/models"]
        if provider_id == "vllm":
            return [f"{base_url}/health", f"{base_url}/v1/models"]
        return [base_url]

    def _probe_models(self, provider_id: str, base_url: str) -> list[str]:
        if httpx is None:
            return []
        try:
            if provider_id == "ollama":
                response = httpx.get(f"{base_url}/api/tags", timeout=1.5)
                if response.status_code < 400:
                    payload = response.json()
                    return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
            if provider_id in {"lmstudio", "vllm", "llamacpp"}:
                response = httpx.get(f"{base_url}/v1/models", timeout=1.5)
                if response.status_code < 400:
                    payload = response.json()
                    model_items = payload.get("data", []) if isinstance(payload, dict) else []
                    return [item.get("id", "") for item in model_items if item.get("id")]
        except Exception:
            return []
        return []

    def test_provider_connectivity(self, provider_id: str, settings: dict[str, Any] | None = None) -> dict[str, Any]:
        settings = settings or {}
        state = {"provider_id": provider_id, "connected": False, "health": "unknown", "latency_ms": None, "models": [], "capabilities": {}, "error": None}
        start = time.perf_counter()
        if provider_id in {"ollama", "lmstudio", "llamacpp", "vllm"}:
            details = self.detect_local_runtime(provider_id, settings.get("base_url"))
            state["connected"] = bool(details.get("available"))
            state["health"] = "healthy" if state["connected"] else "degraded"
            state["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            state["models"] = details.get("models", [])
            state["capabilities"] = details.get("capabilities", self._capability_map(provider_id))
            return state
        if provider_id in {"openai", "anthropic", "google", "groq", "openrouter", "deepseek", "mistral", "cohere", "together", "fireworks", "azure_openai"}:
            if httpx is None:
                state["health"] = "degraded"
                state["error"] = "httpx is not installed"
                state["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
                return state
            api_key = settings.get("api_key") or self._resolve_provider_secret(provider_id)
            if not api_key:
                state["error"] = "missing api key"
                return state
            try:
                response = httpx.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=2.0)
                state["connected"] = response.status_code < 400
                state["health"] = "healthy" if state["connected"] else "degraded"
                state["error"] = None if state["connected"] else response.text[:200]
            except Exception as exc:
                state["error"] = str(exc)
            finally:
                state["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            return state
        state["health"] = "degraded"
        state["error"] = "unsupported provider"
        return state

    def _resolve_provider_secret(self, provider_id: str) -> str | None:
        from .configuration import ProviderConfiguration

        config = ProviderConfiguration({"provider": provider_id})
        return config.get_secret(provider_id)

    def register_provider(self, provider_id: str, settings: dict[str, Any] | None = None, capabilities: dict[str, bool] | None = None) -> dict[str, Any]:
        with self._lock:
            configuration = ModelConfiguration(provider_id=provider_id, settings=settings or {}, defaults={})
            self._provider_manager.add_provider(provider_id, configuration)
            definition = self._definitions.get(provider_id, ProviderDefinition(provider_id, provider_id))
            self._definitions[provider_id] = ProviderDefinition(
                provider_id=provider_id,
                display_name=definition.display_name,
                provider_type=definition.provider_type,
                capabilities={**definition.capabilities, **(capabilities or {})},
                metadata=definition.metadata,
            )
            self._provider_states[provider_id] = {"provider_id": provider_id, "status": "registered", "connected": False, "last_checked": None}
            self._emit("provider.registered", {"provider_id": provider_id, "capabilities": self._definitions[provider_id].capabilities})
            self.persist_state(self._state_path)
            return {"provider_id": provider_id, "capabilities": self._definitions[provider_id].capabilities}

    def _capability_map(self, provider_id: str) -> dict[str, bool]:
        defaults = {
            "ollama": {"chat": True, "streaming": True, "embeddings": True},
            "lmstudio": {"chat": True, "vision": True},
            "llamacpp": {"chat": True},
            "vllm": {"chat": True, "streaming": True},
        }
        return defaults.get(provider_id, {})

    def register_model(self, model_id: str, provider: str, capabilities: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            entry = {
                "model_id": model_id,
                "provider_id": provider,
                "display_name": metadata.get("display_name", model_id) if metadata else model_id,
                "family": metadata.get("family", "generic") if metadata else "generic",
                "context_length": metadata.get("context_length", 8192) if metadata else 8192,
                "pricing": metadata.get("pricing", {}) if metadata else {},
                "vision": bool(metadata.get("vision", False)) if metadata else False,
                "reasoning": bool(metadata.get("reasoning", False)) if metadata else False,
                "tools": bool(metadata.get("tools", False)) if metadata else False,
                "embeddings": bool(metadata.get("embeddings", False)) if metadata else False,
                "audio": bool(metadata.get("audio", False)) if metadata else False,
                "image": bool(metadata.get("image", False)) if metadata else False,
                "streaming": bool(metadata.get("streaming", False)) if metadata else False,
                "json_mode": bool(metadata.get("json_mode", False)) if metadata else False,
                "structured_output": bool(metadata.get("structured_output", False)) if metadata else False,
                "recommended_tasks": list(metadata.get("recommended_tasks", [])) if metadata else [],
                "speed": metadata.get("speed", "medium") if metadata else "medium",
                "quality": metadata.get("quality", "standard") if metadata else "standard",
                "offline_availability": bool(metadata.get("offline_availability", False)) if metadata else False,
                "memory_usage": metadata.get("memory_usage", "medium") if metadata else "medium",
                "license": metadata.get("license", "unknown") if metadata else "unknown",
                "capabilities": list(capabilities or []),
            }
            self._models[model_id] = entry
            self.persist_state(self._state_path)
            return entry

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self._models.get(model_id))

    def list_models(self) -> list[dict[str, Any]]:
        with self._lock:
            return [copy.deepcopy(model) for model in self._models.values()]

    def resolve_default_provider(self, preference: str | None = None) -> str | None:
        with self._lock:
            providers = self.list_providers()
            if not providers:
                return None
            if preference and preference in providers:
                return preference
            return providers[0]

    def get_provider_state(self, provider_id: str) -> dict[str, Any]:
        with self._lock:
            definition = self._definitions.get(provider_id, ProviderDefinition(provider_id, provider_id))
            return {
                "provider_id": provider_id,
                "display_name": definition.display_name,
                "provider_type": definition.provider_type,
                "capabilities": dict(definition.capabilities),
                "registered": provider_id in self._provider_manager._providers,
                "state": dict(self._provider_states.get(provider_id, {})),
            }

    def add_routing_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._routing_rules.append(rule)
            self.persist_state(self._state_path)
            return rule

    def list_routing_rules(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._routing_rules)

    def select_best_provider(self, task: str, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = policy or {}
        with self._lock:
            providers = self.list_provider_details()
            if not providers:
                return {"provider_id": None, "model_id": None}
            if policy.get("offline"):
                for provider_id in ["ollama", "lmstudio", "llamacpp", "vllm"]:
                    provider = next((provider for provider in providers if provider["provider_id"] == provider_id), None)
                    if provider is not None:
                        return {"provider_id": provider["provider_id"], "model_id": self._best_model_for_provider(provider["provider_id"], task)}
            for provider_id in ["openai", "anthropic", "google", "groq", "openrouter", "deepseek", "mistral", "together", "fireworks", "azure_openai", "cohere"]:
                provider = next((provider for provider in providers if provider["provider_id"] == provider_id), None)
                if provider is not None and (provider.get("connected", False) or not policy.get("require_online", True)):
                    return {"provider_id": provider["provider_id"], "model_id": self._best_model_for_provider(provider["provider_id"], task)}
            fallback = next((provider for provider in providers if provider["provider_id"] in {"ollama", "lmstudio", "llamacpp", "vllm"}), None)
            if fallback is not None:
                return {"provider_id": fallback["provider_id"], "model_id": self._best_model_for_provider(fallback["provider_id"], task)}
            return {"provider_id": providers[0]["provider_id"], "model_id": self._best_model_for_provider(providers[0]["provider_id"], task)}

    def _best_model_for_provider(self, provider_id: str, task: str) -> str:
        models = [model for model in self.list_models() if model.get("provider_id") == provider_id]
        if models:
            for model in models:
                tasks = model.get("recommended_tasks", [])
                if task in tasks:
                    return model["model_id"]
            return models[0]["model_id"]
        if provider_id in {"ollama", "lmstudio", "llamacpp", "vllm"}:
            return "llama3"
        return "default"

    def run_offline_fallback(self) -> dict[str, Any]:
        with self._lock:
            selection = self.select_best_provider("chat", {"offline": True, "require_online": False})
            self._emit("provider.offline.fallback", selection)
            return selection

    def persist_state(self, path: str | Path | None = None) -> None:
        target = Path(path or self._state_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "definitions": {provider_id: {"provider_id": definition.provider_id, "display_name": definition.display_name, "provider_type": definition.provider_type, "capabilities": definition.capabilities, "metadata": definition.metadata} for provider_id, definition in self._definitions.items()},
            "models": self._models,
            "provider_states": self._provider_states,
            "routing_rules": self._routing_rules,
            "benchmark_history": self._benchmark_history,
        }
        with target.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def load_state(self, path: str | Path | None = None) -> None:
        target = Path(path or self._state_path)
        if not target.exists():
            return
        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self._definitions = {
                provider_id: ProviderDefinition(
                    provider_id=data.get("provider_id", provider_id),
                    display_name=data.get("display_name", provider_id),
                    provider_type=data.get("provider_type", "cloud"),
                    capabilities=data.get("capabilities", {}),
                    metadata=data.get("metadata", {}),
                )
                for provider_id, data in payload.get("definitions", {}).items()
            }
            self._models = payload.get("models", {})
            self._provider_states = payload.get("provider_states", {})
            self._routing_rules = payload.get("routing_rules", [])
            self._benchmark_history = payload.get("benchmark_history", [])
            for provider_id in self._definitions:
                self._provider_manager.add_provider(provider_id, ModelConfiguration(provider_id=provider_id, settings={}, defaults={}))
        except Exception:
            return
