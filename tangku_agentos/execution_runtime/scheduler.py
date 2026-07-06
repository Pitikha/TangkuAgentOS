from __future__ import annotations

from .interfaces import ExecutionScheduler


class ExecutionScheduler(ExecutionScheduler):
    """Concrete execution scheduler."""

    def schedule(self, session_id: str, cron_expression: str) -> str:
        raise NotImplementedError

    def cancel(self, schedule_id: str) -> None:
        raise NotImplementedError
