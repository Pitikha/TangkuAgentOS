from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from .models import InterfaceEvent


class InterfaceEventManager(ABC):
    """Interface for emitting and subscribing interface events."""

    @abstractmethod
    def publish_event(self, event: InterfaceEvent) -> None:
        ...

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[InterfaceEvent], None]) -> None:
        ...

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[InterfaceEvent], None]) -> None:
        ...

    @abstractmethod
    def list_subscriptions(self, session_id: str) -> list[str]:
        ...
