from __future__ import annotations

from .interfaces import ToolRegistryInterface
from .models import Tool


class ToolRegistry(ToolRegistryInterface):
    """Store registered tools by tool id."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.tool_id] = tool

    def resolve(self, tool_id: str) -> Tool:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(tool_id)
        return tool

    def list(self) -> list[Tool]:
        return list(self._tools.values())
