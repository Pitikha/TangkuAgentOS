from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .models import WorkflowInstance


@dataclass
class WorkflowContext:
    instance_id: str
    workflow_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowContextManager:
    """Simple workflow context provider."""

    def build_context(self, instance: WorkflowInstance) -> WorkflowContext:
        return WorkflowContext(instance_id=instance.instance_id, workflow_id=instance.workflow.workflow_id)
