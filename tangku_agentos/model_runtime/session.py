from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .interfaces import ModelSessionManager
from .models import ModelSession


class ModelSessionManager(ModelSessionManager):
    """Concrete model session manager."""

    def __init__(self) -> None:
        self._sessions: dict[str, ModelSession] = {}

    def create_session(self, model_id: str) -> ModelSession:
        now = datetime.now(timezone.utc)
        session = ModelSession(
            session_id=str(uuid4()),
            model_id=model_id,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=30)).isoformat(),
        )
        self._sessions[session.session_id] = session
        return session

    def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
