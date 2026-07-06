from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .models import PlanningSession


class PlanningSessionManager:
    """Manage planning sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, PlanningSession] = {}
        self._lock = RLock()

    def create_session(self, plan_id: str, *, metadata: dict[str, object] | None = None) -> PlanningSession:
        session = PlanningSession(session_id=str(uuid4()), plan_id=plan_id, metadata=dict(metadata or {}))
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> PlanningSession | None:
        with self._lock:
            return self._sessions.get(session_id)
