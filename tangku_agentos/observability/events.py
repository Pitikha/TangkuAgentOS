from __future__ import annotations

from threading import RLock

from .models import EventTimeline


class EventRecorder:
    """In-process event recorder for observability timelines."""

    def __init__(self) -> None:
        self._events: list[EventTimeline] = []
        self._lock = RLock()

    def record(self, event: EventTimeline) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> list[EventTimeline]:
        with self._lock:
            return list(self._events)
