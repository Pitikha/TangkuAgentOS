from __future__ import annotations

from .interfaces import WorkflowScheduler


class WorkflowSchedulerImpl(WorkflowScheduler):
    """Foundation workflow scheduler."""

    def schedule(self, workflow_id: str, cron_expression: str) -> None:
        pass

    def unschedule(self, workflow_id: str) -> None:
        pass
