from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .models import SecuritySession


class SecuritySessionManager:
    """Track security sessions for runtime operations."""

    def __init__(self) -> None:
        self._sessions: dict[str, SecuritySession] = {}
        self._lock = RLock()

    def create_session(self, subject_id: str, metadata: dict[str, object] | None = None) -> SecuritySession:
        session = SecuritySession(session_id=str(uuid4()), subject_id=subject_id, metadata=metadata or {})
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> SecuritySession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
