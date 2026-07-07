from __future__ import annotations

from uuid import uuid4

from .interfaces import MCPSessionManager
from .models import MCPConnection, MCPSession


class MCPSessionManager(MCPSessionManager):
    """MCP session manager abstraction."""

    def __init__(self) -> None:
        self._sessions: dict[str, MCPSession] = {}

    def create_session(self, connection: MCPConnection) -> MCPSession:
        session = MCPSession(session_id=str(uuid4()), connection=connection, metadata={"status": "active"})
        self._sessions[session.session_id] = session
        return session

    def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
