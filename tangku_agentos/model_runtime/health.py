from __future__ import annotations

from .interfaces import ModelHealthManager


class ModelHealthManager(ModelHealthManager):
    """Concrete model health manager."""

    def __init__(self) -> None:
        self._status: dict[str, dict[str, object]] = {}

    def check_model(self, model_id: str) -> dict[str, object]:
        status = self._status.get(model_id, {"status": "unknown"})
        return {"model_id": model_id, **status}
