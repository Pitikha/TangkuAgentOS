from __future__ import annotations

from collections import deque
from threading import RLock
from typing import Deque, Optional

from .models import WorkflowInstance


class WorkflowQueue:
    """Thread-safe workflow queue for pending instances."""

    def __init__(self) -> None:
        self._queue: Deque[WorkflowInstance] = deque()
        self._lock = RLock()

    def enqueue(self, instance: WorkflowInstance) -> None:
        with self._lock:
            self._queue.append(instance)

    def dequeue(self) -> Optional[WorkflowInstance]:
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def peek(self) -> Optional[WorkflowInstance]:
        with self._lock:
            return self._queue[0] if self._queue else None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)
