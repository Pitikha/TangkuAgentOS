from __future__ import annotations

from threading import RLock
from typing import List


class TaskQueue:
    def __init__(self) -> None:
        self._queue: List[str] = []
        self._lock = RLock()

    def push(self, task_id: str) -> None:
        with self._lock:
            self._queue.append(task_id)

    def pop(self) -> str | None:
        with self._lock:
            return self._queue.pop(0) if self._queue else None

    def list(self) -> List[str]:
        with self._lock:
            return list(self._queue)
