from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Protocol

from .models import Workflow, WorkflowInstance, WorkflowResult, WorkflowState


class WorkflowManagerInterface(ABC):
    """Interface for workflow management operations."""

    @abstractmethod
    def create_workflow(self, workflow: Workflow) -> None:
        ...

    @abstractmethod
    def start_workflow(self, workflow_id: str) -> WorkflowInstance:
        ...

    @abstractmethod
    def stop_workflow(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def pause_workflow(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def resume_workflow(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def cancel_workflow(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def archive_workflow(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Workflow:
        ...


class WorkflowRegistryInterface(ABC):
    """Interface for workflow registry operations."""

    @abstractmethod
    def register(self, workflow: Workflow) -> None:
        ...

    @abstractmethod
    def unregister(self, workflow_id: str) -> None:
        ...

    @abstractmethod
    def get(self, workflow_id: str) -> Workflow:
        ...

    @abstractmethod
    def list(self) -> list[Workflow]:
        ...


class WorkflowExecutor(ABC):
    """Interface for executing workflow instances."""

    @abstractmethod
    def execute(self, instance: WorkflowInstance) -> WorkflowResult:
        ...


class WorkflowScheduler(ABC):
    """Interface for scheduling workflow execution."""

    @abstractmethod
    def schedule(self, workflow_id: str, cron_expression: str) -> None:
        ...

    @abstractmethod
    def unschedule(self, workflow_id: str) -> None:
        ...


class WorkflowBuilder(ABC):
    """Interface for workflow construction and validation."""

    @abstractmethod
    def build(self, workflow: Workflow) -> Workflow:
        ...


class WorkflowTrigger(ABC):
    """Interface for defining workflow triggers."""

    @abstractmethod
    def trigger(self, workflow_id: str) -> None:
        ...


class WorkflowContextProvider(Protocol):
    """Protocol for providing workflow-specific context."""

    def build_context(self, instance: WorkflowInstance) -> "WorkflowContext":
        ...


class WorkflowLifecycleManager(ABC):
    """Interface for workflow lifecycle transitions."""

    @abstractmethod
    def transition(self, instance: WorkflowInstance, state: WorkflowState) -> None:
        ...


class WorkflowHistoryManager(ABC):
    """Interface for workflow history tracking."""

    @abstractmethod
    def record(self, instance: WorkflowInstance, event: str, details: Mapping[str, Any]) -> None:
        ...


class WorkflowQueue(ABC):
    """Interface for workflow queueing."""

    @abstractmethod
    def enqueue(self, instance: WorkflowInstance) -> None:
        ...

    @abstractmethod
    def dequeue(self) -> WorkflowInstance | None:
        ...


class WorkflowEventManager(ABC):
    """Protocol for workflow event management."""

    @abstractmethod
    def publish(self, event_name: str, payload: Mapping[str, Any]) -> None:
        ...
