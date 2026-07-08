from __future__ import annotations

from uuid import uuid4

from .interfaces import ProviderSession


class ProviderSession(ProviderSession):
    """Provider session manager."""

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    def start(self, provider_id: str) -> str:
        session_id = str(uuid4())
        self._sessions[session_id] = provider_id
        return session_id

    def end(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
