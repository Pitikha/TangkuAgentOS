from __future__ import annotations

from .interfaces import MCPTransportLayer
from .models import MCPConnection, MCPResponse


class MCPTransportLayer(MCPTransportLayer):
    """MCP transport layer abstraction."""

    def send(self, connection: MCPConnection, payload: dict[str, str]) -> MCPResponse:
        return MCPResponse(request_id=connection.connection_id, session=None, payload=payload, metadata={"transport": "in-memory"})

    def receive(self, connection: MCPConnection) -> dict[str, str]:
        return {"connection_id": connection.connection_id, "status": "received"}
