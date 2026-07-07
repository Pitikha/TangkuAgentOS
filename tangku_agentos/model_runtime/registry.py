from __future__ import annotations

from typing import Dict

from .interfaces import ModelRegistryInterface
from .models import Model


class ModelRegistry(ModelRegistryInterface):
    """Registry for model definitions."""

    def __init__(self) -> None:
        self._models: Dict[str, Model] = {}

    def register_model(self, model: Model) -> None:
        self._models[model.model_id] = model

    def resolve_model(self, model_id: str) -> Model:
        return self._models[model_id]

    def list_models(self) -> list[Model]:
        return list(self._models.values())
