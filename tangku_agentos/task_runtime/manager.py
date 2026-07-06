from __future__ import annotations

from threading import RLock
from uuid import uuid4


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._lock = RLock()

    def create_task(self, name: str, metadata: dict | None = None) -> str:
        task_id = str(uuid4())
        with self._lock:
            self._tasks[task_id] = {"name": name, "metadata": dict(metadata or {})}
        return task_id

    def get_task(self, task_id: str) -> dict | None:
        with self._lock:
            return self._tasks.get(task_id)
