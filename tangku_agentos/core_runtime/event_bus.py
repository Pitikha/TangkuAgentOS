from __future__ import annotations

import time
from collections import defaultdict
from threading import RLock
from typing import DefaultDict, Dict, List

from .exceptions import EventBusError
from .types import EventHandler, EventPayload, EventRecord


class EventListener:
    """Represents a registered event listener."""

    def __init__(self, handler: EventHandler) -> None:
        self.handler = handler


class EventBus:
    """Core event bus for kernel event publishing and subscription."""

    def __init__(self) -> None:
        self._listeners: DefaultDict[str, List[EventListener]] = defaultdict(list)
        self._history: List[EventRecord] = []
        self._lock = RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if not event_name or not callable(handler):
            raise EventBusError("Event name and handler must be valid.")

        with self._lock:
            self._listeners[event_name].append(EventListener(handler))

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            listeners = self._listeners.get(event_name, [])
            self._listeners[event_name] = [listener for listener in listeners if listener.handler != handler]

    def publish(self, event_name: str, payload: EventPayload | None = None, metadata: Dict[str, object] | None = None) -> EventRecord:
        if not event_name:
            raise EventBusError("Event name must be provided.")

        payload = payload or {}
        record = EventRecord(
            name=event_name,
            payload=payload,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        with self._lock:
            self._history.append(record)
            listeners = list(self._listeners.get(event_name, []))

        errors: list[Exception] = []
        for listener in listeners:
            try:
                listener.handler(event_name, payload)
            except Exception as error:
                errors.append(error)

        if errors:
            raise EventBusError(
                f"{len(errors)} listener(s) failed for event '{event_name}': {errors}"
            )

        return record

    def history(self) -> List[EventRecord]:
        with self._lock:
            return list(self._history)

    def list_listeners(self, event_name: str) -> List[EventHandler]:
        with self._lock:
            return [listener.handler for listener in self._listeners.get(event_name, [])]

    def clear_listeners(self) -> None:
        with self._lock:
            self._listeners.clear()
