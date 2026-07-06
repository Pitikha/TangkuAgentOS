from __future__ import annotations

from .interfaces import ModelLifecycleManager
from .models import Model


class ModelLifecycleManager(ModelLifecycleManager):
    """Concrete model lifecycle manager."""

    def __init__(self) -> None:
        self._deployed: dict[str, Model] = {}

    def deploy(self, model: Model) -> None:
        self._deployed[model.model_id] = model

    def retire(self, model_id: str) -> None:
        self._deployed.pop(model_id, None)
