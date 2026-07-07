from __future__ import annotations

from datetime import datetime
from typing import Dict

from .exceptions import WorkflowEngineError
from .interfaces import WorkflowExecutor
from .models import (
    WorkflowInstance,
    WorkflowResult,
    WorkflowState,
    WorkflowAction,
)


class WorkflowExecutorImpl(WorkflowExecutor):
    """Executor implementation that materializes workflow actions and state transitions."""

    def execute(self, instance: WorkflowInstance) -> WorkflowResult:
        instance.state = WorkflowState.RUNNING
        instance.updated_at = datetime.utcnow().isoformat()

        try:
            result_payload = self._execute_actions(instance)
            completion_status = WorkflowState.COMPLETED
        except Exception as error:
            instance.state = WorkflowState.FAILED
            instance.updated_at = datetime.utcnow().isoformat()
            return WorkflowResult(
                workflow_id=instance.workflow.workflow_id,
                status=WorkflowState.FAILED,
                output={"error": str(error)},
                metadata={"exception_type": type(error).__name__},
            )

        instance.state = completion_status
        instance.updated_at = datetime.utcnow().isoformat()

        return WorkflowResult(
            workflow_id=instance.workflow.workflow_id,
            status=completion_status,
            output=result_payload,
            metadata={"executed_at": datetime.utcnow().isoformat()},
        )

    def _execute_actions(self, instance: WorkflowInstance) -> Dict[str, dict[str, str]]:
        output: Dict[str, dict[str, str]] = {}

        for action in instance.workflow.actions:
            output[action.action_id] = {
                "name": action.descriptor.name,
                "status": "completed",
                "approval": action.descriptor.approval.value,
            }

        if not instance.workflow.actions and instance.workflow.stages:
            output["stages"] = {stage.stage_id: "completed" for stage in instance.workflow.stages}

        output["workflow_id"] = instance.workflow.workflow_id
        output["status"] = instance.state.value
        return output
