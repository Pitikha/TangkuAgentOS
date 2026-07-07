from __future__ import annotations

from threading import RLock

from .interfaces import TrustManager


class TrustManager(TrustManager):
    """Trust manager architecture with simple trust levels."""

    def __init__(self) -> None:
        self._trust: dict[str, float] = {}
        self._lock = RLock()

    def evaluate_trust(self, identity_id: str) -> bool:
        with self._lock:
            return self._trust.get(identity_id, 0.0) >= 0.5

    def set_trust(self, identity_id: str, level: float) -> None:
        with self._lock:
            self._trust[identity_id] = level
