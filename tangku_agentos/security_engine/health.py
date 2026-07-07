from __future__ import annotations

from threading import RLock


class SecurityHealthManager:
    """Provide a lightweight health status surface for the security runtime."""

    def __init__(self) -> None:
        self._status: dict[str, object] = {"status": "healthy"}
        self._lock = RLock()

    def get_health(self) -> dict[str, object]:
        with self._lock:
            return dict(self._status)

    def set_health(self, status: dict[str, object]) -> None:
        with self._lock:
            self._status = dict(status)
