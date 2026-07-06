from __future__ import annotations

from threading import RLock

from .interfaces import MonitoringManager
from .models import EventTimeline


class MonitoringManager(MonitoringManager):
    """Simple in-process monitoring manager for event timelines."""

    def __init__(self) -> None:
        self._timelines: list[EventTimeline] = []
        self._lock = RLock()

    def monitor(self) -> EventTimeline:
        with self._lock:
            timeline = EventTimeline(timeline_id="default", events=[], metadata={})
            self._timelines.append(timeline)
            return timeline

    def snapshot(self) -> list[EventTimeline]:
        with self._lock:
            return list(self._timelines)
