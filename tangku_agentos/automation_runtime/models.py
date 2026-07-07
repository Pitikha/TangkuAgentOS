from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AutomationPolicy(str, Enum):
    SECURITY_AWARE = "security_aware"
    RESOURCE_AWARE = "resource_aware"
    COST_AWARE = "cost_aware"
    WORKSPACE_AWARE = "workspace_aware"
    MULTI_AGENT = "multi_agent"
    APPROVAL_REQUIRED = "approval_required"
    RECOVERY = "recovery"


@dataclass(slots=True)
class AutomationDefinition:
    automation_id: str
    name: str
    enabled: bool = True
    version: str = "0.1.0"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AutomationSession:
    session_id: str
    automation_id: str
    active: bool = False
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobDefinition:
    job_id: str
    name: str
    job_type: str = "one_time"
    parent_job_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobSession:
    session_id: str
    job_id: str
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobContext:
    job_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobHistoryEntry:
    job_id: str
    status: str
    message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class JobLifecycle:
    state: str = "created"
    attempts: int = 0
    last_error: str | None = None


@dataclass(slots=True)
class ScheduleDefinition:
    schedule_id: str
    schedule_type: str
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScheduleHistoryEntry:
    schedule_id: str
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class TriggerDefinition:
    trigger_id: str
    trigger_type: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackgroundTask:
    task_id: str
    name: str
    state: str = "created"
    progress: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackgroundContext:
    task_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackgroundLifecycle:
    state: str = "created"
    retry_count: int = 0
    checkpoint: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "AutomationDefinition",
    "AutomationPolicy",
    "AutomationSession",
    "BackgroundContext",
    "BackgroundLifecycle",
    "BackgroundTask",
    "JobContext",
    "JobDefinition",
    "JobHistoryEntry",
    "JobLifecycle",
    "JobSession",
    "ScheduleDefinition",
    "ScheduleHistoryEntry",
    "TriggerDefinition",
]
