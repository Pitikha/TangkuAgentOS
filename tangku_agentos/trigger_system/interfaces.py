from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import TriggerContext, TriggerResult


class TriggerRegistryInterface(ABC):
    """Interface for trigger registry operations."""

    @abstractmethod
    def register(self, trigger_type: str, handler: Any) -> None:
        ...

    @abstractmethod
    def resolve(self, trigger_type: str) -> Any:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class TriggerManagerInterface(ABC):
    """Interface for trigger management."""

    @abstractmethod
    def register_trigger(self, trigger_type: str, handler: Any) -> None:
        ...

    @abstractmethod
    def trigger(self, trigger_type: str, context: TriggerContext) -> TriggerResult:
        ...


class FileTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class GitTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class TimeTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class WebhookTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class APITrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class WorkflowTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class AgentTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class MemoryTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class UserTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...


class SystemTrigger(ABC):
    @abstractmethod
    def trigger(self, context: TriggerContext) -> TriggerResult:
        ...
