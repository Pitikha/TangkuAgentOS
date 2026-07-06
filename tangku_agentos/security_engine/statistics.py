from __future__ import annotations

from threading import RLock


class SecurityStatisticsManager:
    """Collect lightweight runtime security statistics."""

    def __init__(self) -> None:
        self._stats: dict[str, int] = {}
        self._lock = RLock()

    def record(self, key: str, value: int = 1) -> None:
        with self._lock:
            self._stats[key] = self._stats.get(key, 0) + value

    def get_statistics(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stats)
