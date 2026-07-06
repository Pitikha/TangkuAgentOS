from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any, Callable, Dict, Iterable, Optional

from .exceptions import AgentRuntimeError
from .interfaces import BaseAgent
from .messages import AgentTask, AgentResult
from .scheduler import AgentScheduler
from .types import AgentContext, AgentResourceAllocation, AgentResourceBudget


@dataclass(frozen=True)
class ExecutionResultRecord:
    result: AgentResult
    completed_at: datetime
    duration_seconds: float
    success: bool


class AgentExecutionEngine:
    """Execution engine for managing agent tasks and message dispatch."""

    def __init__(self, scheduler: AgentScheduler, max_workers: int = 4) -> None:
        self._scheduler = scheduler
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._futures: Dict[str, concurrent.futures.Future[AgentResult]] = {}
        self._lock = RLock()
        self._resource_budget = AgentResourceBudget()

    def submit_task(self, agent: BaseAgent, task: AgentTask, callback: Callable[[AgentResult], None] | None = None) -> str:
        self._scheduler.enqueue(task)
        future = self._executor.submit(self._execute_task, agent, task)
        with self._lock:
            self._futures[task.task_id] = future
        if callback:
            future.add_done_callback(lambda fut: callback(fut.result()))
        return task.task_id

    def _execute_task(self, agent: BaseAgent, task: AgentTask) -> AgentResult:
        start = datetime.utcnow()
        if self._scheduler.task_status(task.task_id) == "running":
            try:
                result = agent.handle_task(task)
                duration = (datetime.utcnow() - start).total_seconds()
                return AgentResult(
                    result_id=result.result_id,
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    status=result.status,
                    payload=result.payload,
                    metadata=result.metadata,
                    created_at=result.created_at,
                    updated_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                )
            except Exception as error:
                raise AgentRuntimeError(str(error)) from error
        raise AgentRuntimeError(f"Task {task.task_id} cannot execute because it is not active.")

    def get_result(self, task_id: str) -> AgentResult | None:
        with self._lock:
            future = self._futures.get(task_id)
            if future is None:
                return None
            if future.done():
                return future.result()
            return None

    def cancel_task(self, task_id: str) -> None:
        self._scheduler.cancel(task_id)
        with self._lock:
            future = self._futures.get(task_id)
            if future is not None:
                future.cancel()

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)
        self._scheduler.shutdown()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "active_tasks": len(self._futures),
                "pending_tasks": self._scheduler.queue_size(),
            }
