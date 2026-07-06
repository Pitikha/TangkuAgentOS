from __future__ import annotations

from .interfaces import ToolResolver
from .models import Tool, ToolRequest
from .registry import ToolRegistry


class ToolResolver(ToolResolver):
    """Resolve a tool request against the registry."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()

    def resolve(self, request: ToolRequest) -> Tool:
        return self._registry.resolve(request.tool_id)
