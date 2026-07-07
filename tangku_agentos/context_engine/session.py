from __future__ import annotations

from .models import ContextSession


class ContextSessionManager:
    """Track active context sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, ContextSession] = {}

    def create_session(self, session_id: str) -> None:
        self._sessions[session_id] = ContextSession(session_id=session_id)

    def attach_context(self, session_id: str, context_id: str) -> None:
        session = self._sessions.setdefault(session_id, ContextSession(session_id=session_id))
        if context_id not in session.context_ids:
            session.context_ids.append(context_id)

    def list_contexts(self, session_id: str) -> list[str]:
        session = self._sessions.get(session_id)
        if session is None:
            return []
        return list(session.context_ids)
