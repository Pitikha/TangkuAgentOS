from __future__ import annotations

from .interfaces import ModelRuntimeManager
from .models import Model, ModelRequest, ModelResponse, ModelResult, ModelUsage
from .registry import ModelRegistry
from .resolver import ModelResolver
from .router import ModelRouter


class ModelRuntimeManager(ModelRuntimeManager):
    """Core model runtime manager."""

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        resolver: ModelResolver | None = None,
        router: ModelRouter | None = None,
    ) -> None:
        self._registry = registry or ModelRegistry()
        self._resolver = resolver or ModelResolver(self._registry)
        self._router = router or ModelRouter(self._registry)

    def register_model(self, model: Model) -> None:
        self._registry.register_model(model)

    def select_model(self, capability: str) -> Model:
        for model in self._registry.list_models():
            if any(capability == item.value for item in model.metadata.capabilities):
                return model
        raise KeyError(f"No model registered for capability: {capability}")

    def execute(self, request: ModelRequest) -> ModelResponse:
        model = self._resolver.resolve(request)
        resolved_request = ModelRequest(
            request_id=request.request_id,
            model_id=model.model_id,
            provider_id=request.provider_id,
            payload=request.payload,
            parameters=request.parameters,
            session_id=request.session_id,
            metadata=request.metadata,
        )
        return self._router.route(resolved_request)
