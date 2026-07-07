from __future__ import annotations

from uuid import uuid4

from .interfaces import MCPClient
from .models import MCPConnection, MCPRequest, MCPResponse, MCPServer


class MCPClient(MCPClient):
    """MCP client abstraction."""

    def connect(self, server: MCPServer) -> MCPConnection:
        return MCPConnection(connection_id=str(uuid4()), server=server, metadata={"status": "connected"})

    def request(self, connection: MCPConnection, request: MCPRequest) -> MCPResponse:
        return MCPResponse(
            request_id=request.request_id,
            session=request.session,
            payload={"status": "ok", **request.payload},
            metadata={"connection_id": connection.connection_id},
        )
