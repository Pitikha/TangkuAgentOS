from __future__ import annotations

import heapq
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Callable, Deque, Dict, List, Optional

from .exceptions import AgentRuntimeError
from .messages import AgentTask
from .types import AgentResourceAllocation, AgentResourceBudget


@dataclass(order=True, frozen=True)
class ScheduledTask:
    priority: int
    created_at: datetime = field(compare=False)
    task: AgentTask = field(compare=False)
    timeout_seconds: float | None = field(default=None, compare=False)
    cancellation_token: threading.Event = field(default_factory=threading.Event, compare=False)


class AgentScheduler:
    """Priority-based task scheduler for agent execution."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._queue: list[ScheduledTask] = []
        self._active_tasks: Dict[str, ScheduledTask] = {}
        self._resource_budget: AgentResourceBudget = AgentResourceBudget()
        self._allocation_map: Dict[str, AgentResourceAllocation] = {}
        self._stop_event = threading.Event()

    def set_resource_budget(self, budget: AgentResourceBudget) -> None:
        with self._lock:
            self._resource_budget = budget

    def allocate_resources(self, allocation: AgentResourceAllocation) -> None:
        with self._lock:
            self._allocation_map[allocation.allocation_id] = allocation

    def release_resources(self, allocation_id: str) -> None:
        with self._lock:
            self._allocation_map.pop(allocation_id, None)

    def enqueue(self, task: AgentTask) -> None:
        if not task.task_id or not task.agent_id:
            raise AgentRuntimeError("Task must include task_id and agent_id.")
        with self._lock:
            scheduled = ScheduledTask(
                priority=-task.priority,
                created_at=datetime.utcnow(),
                task=task,
                timeout_seconds=task.timeout_seconds,
            )
            heapq.heappush(self._queue, scheduled)

    def dequeue(self) -> AgentTask | None:
        with self._lock:
            if not self._queue:
                return None
            scheduled = heapq.heappop(self._queue)
            self._active_tasks[scheduled.task.task_id] = scheduled
            return scheduled.task

    def cancel(self, task_id: str) -> None:
        with self._lock:
            if task_id in self._active_tasks:
                self._active_tasks[task_id].cancellation_token.set()
                return
            self._queue = [scheduled for scheduled in self._queue if scheduled.task.task_id != task_id]
            heapq.heapify(self._queue)

    def get_next_task(self) -> AgentTask | None:
        return self.dequeue()

    def task_status(self, task_id: str) -> str:
        with self._lock:
            if task_id in self._active_tasks:
                return "running"
            if any(scheduled.task.task_id == task_id for scheduled in self._queue):
                return "pending"
            return "unknown"

    def enforce_timeouts(self) -> None:
        now = datetime.utcnow().timestamp()
        expired: List[str] = []
        with self._lock:
            for task_id, scheduled in list(self._active_tasks.items()):
                if scheduled.timeout_seconds is not None:
                    start_time = scheduled.created_at.timestamp()
                    if now - start_time > scheduled.timeout_seconds:
                        scheduled.cancellation_token.set()
                        expired.append(task_id)
            for task_id in expired:
                self._active_tasks.pop(task_id, None)

    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)

    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def shutdown(self) -> None:
        self._stop_event.set()
        with self._lock:
            self._queue.clear()
            self._active_tasks.clear()
