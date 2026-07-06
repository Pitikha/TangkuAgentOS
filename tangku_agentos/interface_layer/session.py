from __future__ import annotations

from abc import ABC, abstractmethod

from .models import InterfaceSession


class InterfaceSessionManager(ABC):
    """Interface for managing interface sessions."""

    @abstractmethod
    def create_session(self, session: InterfaceSession) -> None:
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> InterfaceSession:
        ...

    @abstractmethod
    def list_sessions(self) -> list[InterfaceSession]:
        ...

    @abstractmethod
    def refresh_session(self, session_id: str) -> None:
        ...

    @abstractmethod
    def end_session(self, session_id: str) -> None:
        ...


class InterfaceSessionPersistence(ABC):
    @abstractmethod
    def persist(self, session: InterfaceSession) -> None:
        ...

    @abstractmethod
    def restore(self, session_id: str) -> InterfaceSession | None:
        ...

    @abstractmethod
    def list_persisted_sessions(self) -> list[InterfaceSession]:
        ...
