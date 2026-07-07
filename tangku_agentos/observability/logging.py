from __future__ import annotations

from threading import RLock

from .interfaces import LoggingManager
from .models import LogContext, LogEntry, LogSession


class LoggingManager(LoggingManager):
    """Structured in-process logging manager."""

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []
        self._sessions: dict[str, LogSession] = {}
        self._contexts: dict[str, LogContext] = {}
        self._lock = RLock()

    def log(self, entry: LogEntry) -> None:
        with self._lock:
            self._entries.append(entry)
            session_id = entry.metadata.get("session_id")
            if isinstance(session_id, str) and session_id in self._sessions:
                self._sessions[session_id] = LogSession(session_id=session_id, entries=list(self._sessions[session_id].entries) + [entry])
            elif isinstance(session_id, str):
                self._sessions[session_id] = LogSession(session_id=session_id, entries=[entry])

    def snapshot(self) -> list[LogEntry]:
        with self._lock:
            return list(self._entries)

    def session(self, session_id: str) -> LogSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def context(self, context_id: str) -> LogContext | None:
        with self._lock:
            return self._contexts.get(context_id)
