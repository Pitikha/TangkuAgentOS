from __future__ import annotations

from threading import RLock

from .interfaces import TimelineManager
from .models import EventTimeline


class TimelineManager(TimelineManager):
    """In-process timeline manager for event sequences."""

    def __init__(self) -> None:
        self._timelines: list[EventTimeline] = []
        self._lock = RLock()

    def add_event(self, event: EventTimeline) -> None:
        with self._lock:
            self._timelines.append(event)

    def snapshot(self) -> list[EventTimeline]:
        with self._lock:
            return list(self._timelines)
