from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskMetadata:
    task_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskDependency:
    task_id: str
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskPriority:
    task_id: str
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRecord:
    task_id: str
    timestamp: str
    status: TaskStatus
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Subtask:
    subtask_id: str
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Milestone:
    milestone_id: str
    goal_id: str
    description: str = ""
    completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Objective:
    objective_id: str
    goal_id: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Goal:
    goal_id: str
    name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Task:
    task_id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[TaskDependency] = field(default_factory=list)
    priority: TaskPriority | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
