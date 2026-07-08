from __future__ import annotations

from threading import RLock


class DecisionEvaluator:
    def __init__(self) -> None:
        self._lock = RLock()

    def evaluate(self, decision_id: str, context: dict[str, object] | None = None) -> dict[str, object]:
        with self._lock:
            return {"decision_id": decision_id, "outcome": "accepted", "context": dict(context or {})}
