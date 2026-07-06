from __future__ import annotations

from typing import Any

from ..provider_runtime.manager import ProviderManager
from .interfaces import ModelRouter
from .models import ModelRequest, ModelResponse, ModelResult, ModelUsage
from .registry import ModelRegistry


class ModelRouter(ModelRouter):
    """Concrete model request router."""

    def __init__(self, registry: ModelRegistry | None = None, provider_manager: ProviderManager | None = None) -> None:
        self._registry = registry or ModelRegistry()
        self._provider_manager = provider_manager

    def route(self, request: ModelRequest) -> ModelResponse:
        model_id = request.model_id or "default"
        provider_id = request.provider_id or "openai"
        adapter = None
        if self._provider_manager is not None:
            adapter = self._provider_manager.get_adapter(provider_id)

        if adapter is not None and hasattr(adapter, "send"):
            normalized = {
                "request_id": request.request_id,
                "model": model_id,
                "input": request.payload.get("messages") or request.payload.get("prompt") or request.payload,
                "parameters": request.parameters or {},
                "stream": bool(request.payload.get("stream", False)),
                "image": bool(request.payload.get("image", False)),
                "tool_calls": request.payload.get("tool_calls", []),
                "metadata": request.metadata,
            }
            response = adapter.send(normalized)
            success = bool(response.get("success", False))
            output = dict(response.get("output", {}))
            metadata = dict(response.get("metadata", {}))
            usage_payload = response.get("usage") or {}
            usage = ModelUsage(
                model_id=model_id,
                total_requests=1,
                total_tokens=int(usage_payload.get("total_tokens", 0)),
                total_cost=float(usage_payload.get("cost", 0.0)),
                details=usage_payload,
            )
            result = ModelResult(success=success, output=output, metadata=metadata, usage=usage)
            return ModelResponse(request_id=request.request_id, result=result, metadata={"provider_id": provider_id, **metadata})

        usage = ModelUsage(model_id=model_id, total_requests=1)
        result = ModelResult(
            success=True,
            output={"model_id": model_id, "request_id": request.request_id, "status": "queued"},
            usage=usage,
        )
        return ModelResponse(request_id=request.request_id, result=result, metadata={"provider_id": provider_id})
