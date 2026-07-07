from __future__ import annotations

from .models import Tool, ToolStatus


class ToolLifecycleManager:
    """Manage the lifecycle state of registered tools."""

    def __init__(self) -> None:
        self._states: dict[str, ToolStatus] = {}

    def enable(self, tool: Tool) -> None:
        self._states[tool.tool_id] = ToolStatus.AVAILABLE

    def disable(self, tool: Tool) -> None:
        self._states[tool.tool_id] = ToolStatus.OFFLINE

    def get_status(self, tool_id: str) -> ToolStatus:
        return self._states.get(tool_id, ToolStatus.AVAILABLE)
