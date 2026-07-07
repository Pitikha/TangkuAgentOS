from __future__ import annotations

from threading import RLock
from time import perf_counter


class PerformanceManager:
    """Records internal timing and resource observations."""

    def __init__(self) -> None:
        self._timings: dict[str, list[float]] = {}
        self._lock = RLock()

    def record_timing(self, name: str, value: float) -> None:
        with self._lock:
            self._timings.setdefault(name, []).append(value)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return {k: v[-1] for k, v in self._timings.items() if v}

    def timer(self, name: str):
        return _PerformanceTimer(self, name)


class _PerformanceTimer:
    def __init__(self, manager: PerformanceManager, name: str) -> None:
        self._manager = manager
        self._name = name
        self._started = perf_counter()

    def __enter__(self) -> "_PerformanceTimer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        elapsed = perf_counter() - self._started
        self._manager.record_timing(self._name, elapsed)
