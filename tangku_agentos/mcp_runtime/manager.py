from __future__ import annotations

from .interfaces import MCPManagerInterface
from .models import MCPServer


class MCPManager(MCPManagerInterface):
    """MCP manager foundation."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}

    def register_server(self, server: MCPServer) -> None:
        self._servers[server.server_id] = server

    def get_server(self, server_id: str) -> MCPServer:
        return self._servers[server_id]

    def list_servers(self) -> list[MCPServer]:
        return list(self._servers.values())

    def deregister_server(self, server_id: str) -> None:
        self._servers.pop(server_id, None)
