from __future__ import annotations

from typing import Dict

from .interfaces import TaskManagerInterface
from .models import Task


class TaskManager(TaskManagerInterface):
    """Manager for task system operations."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def create_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def list_tasks(self) -> list[Task]:
        return list(self._tasks.values())
