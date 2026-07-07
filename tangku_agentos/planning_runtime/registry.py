from __future__ import annotations

from threading import RLock

from .models import Plan


class PlanningRegistry:
    """In-memory registry for plans."""

    def __init__(self) -> None:
        self._plans: dict[str, Plan] = {}
        self._lock = RLock()

    def register(self, plan: Plan) -> None:
        with self._lock:
            self._plans[plan.plan_id] = plan

    def get(self, plan_id: str) -> Plan | None:
        with self._lock:
            return self._plans.get(plan_id)
