from __future__ import annotations

from dataclasses import asdict
from threading import RLock
from typing import Any

from .models import TelemetryRecord, TelemetrySession


class TelemetryManager:
    """In-process telemetry collector for internal runtime signals."""

    def __init__(self) -> None:
        self._records: list[TelemetryRecord] = []
        self._sessions: dict[str, TelemetrySession] = {}
        self._lock = RLock()

    def collect(self, source: str, payload: dict[str, Any], *, session_id: str | None = None) -> TelemetryRecord:
        with self._lock:
            record = TelemetryRecord(source=source, payload=payload, session_id=session_id)
            self._records.append(record)
            if session_id is not None:
                self._sessions.setdefault(session_id, TelemetrySession(session_id=session_id))
            return record

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [asdict(record) for record in self._records]

    def sessions(self) -> list[TelemetrySession]:
        with self._lock:
            return list(self._sessions.values())
