from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import AutomationDefinition, AutomationSessionModel


class AutomationManagerInterface(ABC):
    """Interface for automation platform management."""

    @abstractmethod
    def register_automation(self, automation: AutomationDefinition) -> None:
        ...

    @abstractmethod
    def schedule_automation(self, automation_id: str) -> None:
        ...

    @abstractmethod
    def enqueue_automation(self, automation_id: str) -> None:
        ...

    @abstractmethod
    def start_session(self, session_id: str, automation_id: str) -> AutomationSessionModel:
        ...


class AutomationRegistryInterface(ABC):
    @abstractmethod
    def register(self, automation: AutomationDefinition) -> None:
        ...

    @abstractmethod
    def resolve(self, automation_id: str) -> AutomationDefinition:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class AutomationScheduler(ABC):
    @abstractmethod
    def schedule(self, automation_id: str, cron_expression: str) -> None:
        ...

    @abstractmethod
    def unschedule(self, automation_id: str) -> None:
        ...


class AutomationQueue(ABC):
    @abstractmethod
    def enqueue(self, automation_id: str) -> None:
        ...

    @abstractmethod
    def dequeue(self) -> str | None:
        ...


class AutomationExecutor(ABC):
    @abstractmethod
    def execute(self, automation: AutomationDefinition) -> dict[str, Any]:
        ...


class AutomationContext(ABC):
    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def update_context(self, updates: dict[str, Any]) -> None:
        ...


class AutomationSession(ABC):
    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def end(self) -> None:
        ...

    @abstractmethod
    def get_status(self) -> str:
        ...


class AutomationType(ABC):
    @abstractmethod
    def get_type(self) -> str:
        ...
