from __future__ import annotations

from .interfaces import MCPRegistryInterface
from .models import MCPResource


class MCPRegistry(MCPRegistryInterface):
    """MCP registry foundation."""

    def __init__(self) -> None:
        self._resources: dict[str, MCPResource] = {}

    def register(self, resource: MCPResource) -> None:
        self._resources[resource.resource_id] = resource

    def resolve(self, key: str) -> MCPResource:
        return self._resources[key]
