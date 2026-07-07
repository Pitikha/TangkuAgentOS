from __future__ import annotations

from .interfaces import MCPDiscoveryManager
from .models import MCPResource


class MCPDiscoveryManager(MCPDiscoveryManager):
    """MCP discovery manager abstraction."""

    def __init__(self) -> None:
        self._resources: list[MCPResource] = []

    def discover(self) -> list[MCPResource]:
        return list(self._resources)
