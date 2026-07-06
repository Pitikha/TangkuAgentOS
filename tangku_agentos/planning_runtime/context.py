from __future__ import annotations

from threading import RLock

from .models import PlanningContext


class PlanningContextManager:
    """Manage planning context state."""

    def __init__(self) -> None:
        self._contexts: dict[str, PlanningContext] = {}
        self._lock = RLock()

    def set_context(self, context: PlanningContext) -> None:
        with self._lock:
            self._contexts[context.context_id] = context

    def get_context(self, context_id: str) -> PlanningContext | None:
        with self._lock:
            return self._contexts.get(context_id)
