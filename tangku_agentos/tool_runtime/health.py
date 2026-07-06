from __future__ import annotations

from .interfaces import ToolHealthManager
from .models import ToolStatus


class ToolHealthManager(ToolHealthManager):
    """Report tool health status using a simple in-memory map."""

    def __init__(self) -> None:
        self._health: dict[str, ToolStatus] = {}

    def check_health(self, tool_id: str) -> ToolStatus:
        return self._health.get(tool_id, ToolStatus.AVAILABLE)

    def set_health(self, tool_id: str, status: ToolStatus) -> None:
        self._health[tool_id] = status
