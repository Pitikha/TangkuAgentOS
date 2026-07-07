from __future__ import annotations

from .interfaces import ToolPermissionManager
from .models import Tool


class ToolPermissionManager(ToolPermissionManager):
    """Authorize tool actions using a simple allow-list."""

    def __init__(self) -> None:
        self._allowed: set[tuple[str, str]] = set()

    def authorize(self, tool: Tool, action: str) -> bool:
        return (tool.tool_id, action) in self._allowed

    def allow(self, tool: Tool, action: str) -> None:
        self._allowed.add((tool.tool_id, action))
