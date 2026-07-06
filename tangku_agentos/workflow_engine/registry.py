from __future__ import annotations

from threading import RLock
from typing import Dict

from .interfaces import WorkflowRegistryInterface
from .models import Workflow
from .exceptions import WorkflowRegistryError


class WorkflowRegistry(WorkflowRegistryInterface):
    """Registry for storing workflow definitions."""

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
        self._lock = RLock()

    def register(self, workflow: Workflow) -> None:
        with self._lock:
            self._workflows[workflow.workflow_id] = workflow

    def unregister(self, workflow_id: str) -> None:
        with self._lock:
            self._workflows.pop(workflow_id, None)

    def get(self, workflow_id: str) -> Workflow:
        with self._lock:
            workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowRegistryError(f"Workflow not found: {workflow_id}")
        return workflow

    def list(self) -> list[Workflow]:
        with self._lock:
            return list(self._workflows.values())
