from __future__ import annotations

from .interfaces import MCPServerAdapter


class MCPServerAdapter(MCPServerAdapter):
    """MCP server adapter abstraction."""

    def __init__(self) -> None:
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False
