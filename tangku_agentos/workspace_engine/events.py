from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class WorkspaceEventType(Enum):
    CREATED = 'workspace.created'
    UPDATED = 'workspace.updated'
    SCANNED = 'workspace.scanned'
    INDEXED = 'workspace.indexed'
    ANALYZED = 'workspace.analyzed'
    ARCHIVED = 'workspace.archived'


class WorkspaceEventPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class WorkspaceEvent:
    event_type: WorkspaceEventType
    workspace_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: WorkspaceEventPriority = WorkspaceEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
