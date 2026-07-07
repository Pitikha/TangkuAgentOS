from __future__ import annotations

from abc import ABC, abstractmethod

from .models import InterfaceContext


class InterfaceStateManager(ABC):
    """Interface for managing interface state."""

    @abstractmethod
    def get_state(self, session_id: str) -> dict[str, object]:
        ...

    @abstractmethod
    def set_state(self, session_id: str, state: dict[str, object]) -> None:
        ...

    @abstractmethod
    def snapshot_state(self, session_id: str) -> dict[str, object]:
        ...

    @abstractmethod
    def restore_state(self, session_id: str) -> None:
        ...

    @abstractmethod
    def persist_state(self, session_id: str, context: InterfaceContext) -> None:
        ...
