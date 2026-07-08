from __future__ import annotations

from threading import RLock

from .models import DecisionMetadata


class DecisionRegistry:
    def __init__(self) -> None:
        self._decisions: dict[str, DecisionMetadata] = {}
        self._lock = RLock()

    def register(self, decision: DecisionMetadata) -> None:
        with self._lock:
            self._decisions[decision.decision_id] = decision

    def get(self, decision_id: str) -> DecisionMetadata | None:
        with self._lock:
            return self._decisions.get(decision_id)
