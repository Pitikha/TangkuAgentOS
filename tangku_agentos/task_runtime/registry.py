from __future__ import annotations

from threading import RLock


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._lock = RLock()

    def register(self, task_id: str, data: dict) -> None:
        with self._lock:
            self._tasks[task_id] = data

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            return self._tasks.get(task_id)
