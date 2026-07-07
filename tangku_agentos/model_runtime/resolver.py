from __future__ import annotations

from .interfaces import ModelResolver
from .models import Model, ModelRequest
from .registry import ModelRegistry


class ModelResolver(ModelResolver):
    """Concrete model resolver."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self._registry = registry or ModelRegistry()

    def resolve(self, request: ModelRequest) -> Model:
        if request.model_id:
            return self._registry.resolve_model(request.model_id)
        models = self._registry.list_models()
        if not models:
            raise KeyError("No models available for resolution")
        return models[0]
