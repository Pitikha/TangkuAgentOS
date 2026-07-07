from __future__ import annotations

from .interfaces import ToolStatisticsManager


class ToolStatisticsManager(ToolStatisticsManager):
    """Collect simple tool usage statistics."""

    def __init__(self) -> None:
        self._stats: dict[str, dict[str, str]] = {}

    def record_usage(self, tool_id: str, data: dict[str, str]) -> None:
        counts = self._stats.setdefault(tool_id, {})
        for key, value in data.items():
            counts[key] = value

    def get_statistics(self, tool_id: str) -> dict[str, str]:
        return dict(self._stats.get(tool_id, {}))
