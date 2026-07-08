from __future__ import annotations

from threading import RLock
from typing import List

from .models import DecisionMetadata


class DecisionHistory:
    def __init__(self) -> None:
        self._history: List[DecisionMetadata] = []
        self._lock = RLock()

    def append(self, decision: DecisionMetadata) -> None:
        with self._lock:
            self._history.append(decision)

    def list(self) -> List[DecisionMetadata]:
        with self._lock:
            return list(self._history)
