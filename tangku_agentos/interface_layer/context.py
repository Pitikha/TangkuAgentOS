from __future__ import annotations

from abc import ABC, abstractmethod

from .models import InterfaceContext


class InterfaceContextManager(ABC):
    """Interface for managing interface context."""

    @abstractmethod
    def get_context(self, session_id: str) -> InterfaceContext:
        ...

    @abstractmethod
    def update_context(self, session_id: str, updates: dict[str, object]) -> None:
        ...

    @abstractmethod
    def sync_context(self, session_id: str, remote_context: InterfaceContext) -> InterfaceContext:
        ...

    @abstractmethod
    def clear_context(self, session_id: str) -> None:
        ...
