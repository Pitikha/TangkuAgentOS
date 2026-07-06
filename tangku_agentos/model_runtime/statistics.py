from __future__ import annotations

from .interfaces import ModelStatisticsManager


class ModelStatisticsManager(ModelStatisticsManager):
    """Concrete model statistics manager."""

    def __init__(self) -> None:
        self._statistics: dict[str, dict[str, object]] = {}

    def record_usage(self, model_id: str, usage: dict[str, object]) -> None:
        current = self._statistics.get(model_id, {})
        merged = dict(current)
        for key, value in usage.items():
            if isinstance(value, (int, float)) and isinstance(merged.get(key), (int, float)):
                merged[key] = int(merged[key]) + int(value)
            else:
                merged[key] = value
        self._statistics[model_id] = merged

    def get_statistics(self, model_id: str) -> dict[str, object]:
        return dict(self._statistics.get(model_id, {}))
