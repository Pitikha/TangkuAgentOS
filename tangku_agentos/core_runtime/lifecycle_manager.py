from __future__ import annotations

from threading import RLock
from typing import Callable, Iterable

from .constants import LifecycleEvent
from .exceptions import LifecycleError
from .types import EventPayload


class LifecycleManager:
    """Core lifecycle manager for kernel state transitions."""

    def __init__(self) -> None:
        self._event_handlers: dict[LifecycleEvent, list[Callable[[EventPayload], None]]] = {
            event: [] for event in LifecycleEvent
        }
        self._state: LifecycleEvent = LifecycleEvent.STOPPED
        self._lock = RLock()

    @property
    def state(self) -> LifecycleEvent:
        with self._lock:
            return self._state

    def register_handler(self, event: LifecycleEvent, handler: Callable[[EventPayload], None]) -> None:
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")
        with self._lock:
            self._event_handlers[event].append(handler)

    def deregister_handler(self, event: LifecycleEvent, handler: Callable[[EventPayload], None]) -> None:
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")
        with self._lock:
            self._event_handlers[event] = [h for h in self._event_handlers[event] if h != handler]

    def trigger(self, event: LifecycleEvent, payload: EventPayload | None = None) -> None:
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")

        payload = payload or {}
        with self._lock:
            self._state = event
            handlers = list(self._event_handlers[event])

        errors: list[Exception] = []
        for handler in handlers:
            try:
                handler(payload)
            except Exception as error:
                errors.append(error)

        if errors:
            with self._lock:
                self._state = LifecycleEvent.FAILED
            raise LifecycleError(
                f"{len(errors)} lifecycle handler(s) failed for event {event}: {errors}"
            )

    def supported_events(self) -> Iterable[LifecycleEvent]:
        return list(self._event_handlers.keys())

    def is_running(self) -> bool:
        return self.state == LifecycleEvent.RUNNING

    def status(self) -> dict[str, str]:
        return {
            "state": self.state.value,
            "supported_events": ", ".join(event.value for event in self.supported_events()),
        }
