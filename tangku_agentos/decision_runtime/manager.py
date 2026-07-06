from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .models import DecisionMetadata


class DecisionManager:
    def __init__(self) -> None:
        self._decisions: dict[str, DecisionMetadata] = {}
        self._lock = RLock()

    def create_decision(self, name: str, context: dict[str, object] | None = None) -> DecisionMetadata:
        decision_id = str(uuid4())
        meta = DecisionMetadata(decision_id=decision_id, name=name, metadata=dict(context or {}))
        with self._lock:
            self._decisions[decision_id] = meta
        return meta

    def get_decision(self, decision_id: str) -> DecisionMetadata | None:
        with self._lock:
            return self._decisions.get(decision_id)
