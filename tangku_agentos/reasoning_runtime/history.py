from __future__ import annotations

from threading import RLock

from .models import ReasoningTrace


class ReasoningHistory:
    """Store reasoning execution history."""

    def __init__(self) -> None:
        self._history: list[ReasoningTrace] = []
        self._lock = RLock()

    def append(self, trace: ReasoningTrace) -> None:
        with self._lock:
            self._history.append(trace)

    def list(self) -> list[ReasoningTrace]:
        with self._lock:
            return list(self._history)
