from __future__ import annotations

from typing import Dict, List

from .interfaces import WorkflowHistoryManager
from .models import WorkflowInstance


class WorkflowHistoryManagerImpl(WorkflowHistoryManager):
    """Foundation workflow history manager."""

    def __init__(self) -> None:
        self._history: Dict[str, List[dict[str, str]]] = {}

    def record(self, instance: WorkflowInstance, event: str, details: dict[str, str]) -> None:
        self._history.setdefault(instance.instance_id, []).append({"event": event, **details})

    def list_history(self, instance_id: str) -> List[dict[str, str]]:
        return self._history.get(instance_id, [])
