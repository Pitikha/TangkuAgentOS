from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Dict, Iterable, Optional

from .exceptions import AgentRuntimeError
from .types import AgentSessionInfo, AgentMetadata


class AgentSessionManager:
    """Manages agent-specific sessions and lifecycle metadata."""

    def __init__(self) -> None:
        self._sessions: Dict[str, AgentSessionInfo] = {}
        self._lock = RLock()

    def create_session(self, session: AgentSessionInfo) -> AgentSessionInfo:
        with self._lock:
            if session.session_id in self._sessions:
                raise AgentRuntimeError(f"Session already exists: {session.session_id}")
            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> AgentSessionInfo:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise AgentRuntimeError(f"Session not found: {session_id}")
            return session

    def list_sessions(self) -> list[AgentSessionInfo]:
        with self._lock:
            return list(self._sessions.values())

    def refresh_session(self, session_id: str, metadata: dict[str, Any] | None = None) -> AgentSessionInfo:
        with self._lock:
            session = self.get_session(session_id)
            updated_metadata = session.metadata.copy()
            if metadata:
                updated_metadata.update(metadata)
            session.updated_at = datetime.utcnow()
            session.metadata = updated_metadata
            return session

    def end_session(self, session_id: str) -> None:
        with self._lock:
            session = self.get_session(session_id)
            session.active = False
            session.updated_at = datetime.utcnow()

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
