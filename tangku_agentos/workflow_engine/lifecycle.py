from __future__ import annotations

from .interfaces import WorkflowLifecycleManager
from .models import WorkflowInstance, WorkflowState


class WorkflowLifecycleManagerImpl(WorkflowLifecycleManager):
    """Foundation workflow lifecycle manager."""

    def transition(self, instance: WorkflowInstance, state: WorkflowState) -> None:
        instance.state = state
