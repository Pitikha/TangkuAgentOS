from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

from .interfaces import WorkflowEventManager


class WorkflowEventType(Enum):
    CREATED = "workflow.created"
    STARTED = "workflow.started"
    PAUSED = "workflow.paused"
    RESUMED = "workflow.resumed"
    COMPLETED = "workflow.completed"
    FAILED = "workflow.failed"
    CANCELLED = "workflow.cancelled"
    ARCHIVED = "workflow.archived"
    TRIGGERED = "workflow.triggered"


class WorkflowEventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class WorkflowEvent:
    event_type: WorkflowEventType
    workflow_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: WorkflowEventPriority = WorkflowEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowEventManagerImpl(WorkflowEventManager):
    """Simple in-process workflow event manager."""

    def __init__(self) -> None:
        self._events: Dict[str, list[Dict[str, Any]]] = {}

    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        self._events.setdefault(event_name, []).append(payload or {})

    def list_events(self, event_name: str) -> list[Dict[str, Any]]:
        return list(self._events.get(event_name, []))
