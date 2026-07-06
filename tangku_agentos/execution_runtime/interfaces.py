from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import ExecutionContext, ExecutionHistory, ExecutionResult, ExecutionSession


class ExecutionManager(ABC):
    """Interface for execution runtime management."""

    @abstractmethod
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...

    @abstractmethod
    def execute_async(self, context: ExecutionContext) -> str:
        ...

    @abstractmethod
    def cancel(self, execution_id: str) -> None:
        ...

    @abstractmethod
    def resume(self, execution_id: str) -> ExecutionResult:
        ...


class ExecutionQueue(ABC):
    """Interface for execution queuing."""

    @abstractmethod
    def enqueue(self, session: ExecutionSession) -> str:
        ...

    @abstractmethod
    def dequeue(self) -> ExecutionSession | None:
        ...


class ExecutionSession(ABC):
    """Interface representing an execution session."""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def end(self) -> None:
        ...


class ExecutionContext(ABC):
    """Interface for execution context."""

    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def update_context(self, updates: dict[str, Any]) -> None:
        ...


class ExecutionScheduler(ABC):
    """Interface for scheduling executions."""

    @abstractmethod
    def schedule(self, session_id: str, cron_expression: str) -> str:
        ...

    @abstractmethod
    def cancel(self, schedule_id: str) -> None:
        ...


class ExecutionHistory(ABC):
    """Interface for execution history tracking."""

    @abstractmethod
    def record(self, session: ExecutionSession, result: ExecutionResult) -> None:
        ...

    @abstractmethod
    def list_history(self, session_id: str) -> list[ExecutionHistory]:
        ...


class ExecutionRecovery(ABC):
    """Interface for execution recovery."""

    @abstractmethod
    def checkpoint(self, session_id: str) -> str:
        ...

    @abstractmethod
    def resume(self, checkpoint_id: str) -> ExecutionSession:
        ...


class ExecutionResult(ABC):
    """Interface for execution results."""

    @abstractmethod
    def get_result(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def is_success(self) -> bool:
        ...
