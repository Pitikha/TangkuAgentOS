from __future__ import annotations

from .interfaces import ToolManagerInterface
from .models import Tool
from .registry import ToolRegistry


class ToolManager(ToolManagerInterface):
    """Coordinate registration and lookup for tools in the runtime."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()
        self._tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        self._registry.register(tool)
        self._tools[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Tool:
        return self._registry.resolve(tool_id)

    def list_tools(self) -> list[Tool]:
        return self._registry.list()

    def remove_tool(self, tool_id: str) -> None:
        self._tools.pop(tool_id, None)
