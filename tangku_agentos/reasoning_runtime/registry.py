from __future__ import annotations

from threading import RLock

from .models import ReasoningContext, ReasoningSession


class ReasoningRegistry:
    """Registry for reasoning contexts and sessions."""

    def __init__(self) -> None:
        self._contexts: dict[str, ReasoningContext] = {}
        self._sessions: dict[str, ReasoningSession] = {}
        self._lock = RLock()

    def register_context(self, context: ReasoningContext) -> None:
        with self._lock:
            self._contexts[context.context_id] = context

    def register_session(self, session: ReasoningSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def get_context(self, context_id: str) -> ReasoningContext | None:
        with self._lock:
            return self._contexts.get(context_id)

    def get_session(self, session_id: str) -> ReasoningSession | None:
        with self._lock:
            return self._sessions.get(session_id)
