from __future__ import annotations

from threading import RLock
from typing import Any, Callable, Dict, List


class EventSubscriptionSDK:
    def __init__(self) -> None:
        self._subscriptions: List[str] = []
        self._lock = RLock()

    def subscribe(self, event_name: str) -> None:
        with self._lock:
            self._subscriptions.append(event_name)


class EventPublisherSDK:
    def __init__(self) -> None:
        self._events: List[tuple[str, Dict[str, Any]]] = []
        self._lock = RLock()

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._events.append((event_name, payload))


class EventFilterSDK:
    def __init__(self) -> None:
        self._filters: Dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._lock = RLock()

    def register(self, event_name: str, callback: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        with self._lock:
            self._filters[event_name] = callback


class EventMiddleware:
    def __init__(self) -> None:
        self._transforms: Dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._lock = RLock()

    def add_transform(self, event_name: str, callback: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        with self._lock:
            self._transforms[event_name] = callback

    def handle(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            transform = self._transforms.get(event_name)
            return transform(payload) if transform else payload
