from __future__ import annotations

from threading import RLock


class PlanningHealthManager:
    """Expose simple health information for the planning runtime."""

    def __init__(self) -> None:
        self._status: dict[str, object] = {"status": "healthy"}
        self._lock = RLock()

    def get_health(self) -> dict[str, object]:
        with self._lock:
            return dict(self._status)
