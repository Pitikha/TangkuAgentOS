from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .models import Goal, Milestone, Objective, Subtask, Task, TaskDependency, TaskMetadata, TaskPriority, ExecutionRecord


class TaskManagerInterface(ABC):
    """Interface for task management."""

    @abstractmethod
    def create_task(self, task: Task) -> None:
        ...

    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        ...

    @abstractmethod
    def list_tasks(self) -> list[Task]:
        ...


class TaskQueue(ABC):
    @abstractmethod
    def enqueue(self, task_id: str) -> None:
        ...

    @abstractmethod
    def dequeue(self) -> str | None:
        ...


class TaskScheduler(ABC):
    @abstractmethod
    def schedule(self, task_id: str, cron_expression: str) -> None:
        ...

    @abstractmethod
    def unschedule(self, task_id: str) -> None:
        ...


class TaskDispatcher(ABC):
    @abstractmethod
    def dispatch(self, task_id: str) -> None:
        ...


class TaskPriority(ABC):
    @abstractmethod
    def evaluate(self, task: Task) -> int:
        ...


class TaskDependency(ABC):
    @abstractmethod
    def resolve(self, task: Task) -> list[Task]:
        ...


class TaskRecovery(ABC):
    @abstractmethod
    def recover(self, task_id: str) -> None:
        ...


class TaskSession(ABC):
    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def end(self) -> None:
        ...


class TaskMetadata(ABC):
    @abstractmethod
    def add_metadata(self, task_id: str, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_metadata(self, task_id: str) -> dict[str, Any]:
        ...


class ExecutionRecord(ABC):
    @abstractmethod
    def record_execution(self, task_id: str, record: ExecutionRecord) -> None:
        ...


class TaskPriorityEvaluator(ABC):
    @abstractmethod
    def evaluate_priority(self, task: Task) -> int:
        ...
