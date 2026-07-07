from __future__ import annotations

from threading import RLock

from .models import PlanState


class PlanningLifecycleManager:
    """Track plan lifecycle transitions."""

    def __init__(self) -> None:
        self._states: dict[str, PlanState] = {}
        self._lock = RLock()

    def set_state(self, plan_id: str, state: PlanState) -> None:
        with self._lock:
            self._states[plan_id] = state

    def get_state(self, plan_id: str) -> PlanState | None:
        with self._lock:
            return self._states.get(plan_id)
