from __future__ import annotations

from threading import RLock

from .interfaces import HealthManager
from .models import HealthReport


class HealthManager(HealthManager):
    """Component health manager with readiness and liveness-style state."""

    def __init__(self) -> None:
        self._components: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def check_health(self) -> HealthReport:
        with self._lock:
            return HealthReport(overall_status="healthy", details=dict(self._components))

    def set_component_status(self, name: str, status: str, details: dict[str, object] | None = None) -> None:
        with self._lock:
            self._components[name] = {"status": status, **(details or {})}

    def snapshot(self) -> dict[str, dict[str, object]]:
        with self._lock:
            return {k: dict(v) for k, v in self._components.items()}
