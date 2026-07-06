from __future__ import annotations

from .interfaces import WorkflowLifecycleManager
from .models import WorkflowInstance, WorkflowState


class WorkflowStateManager(WorkflowLifecycleManager):
    """Workflow state manager for lifecycle transitions."""

    def transition(self, instance: WorkflowInstance, state: WorkflowState) -> None:
        instance.state = state
