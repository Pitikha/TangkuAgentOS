from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .interfaces import TraceManager
from .models import Trace


class TraceManager(TraceManager):
    """In-process trace manager with parent-child span support."""

    def __init__(self) -> None:
        self._traces: dict[str, Trace] = {}
        self._lock = RLock()

    def start_trace(self, name: str, *, parent_span_id: str | None = None, metadata: dict[str, object] | None = None) -> Trace:
        with self._lock:
            trace = Trace(trace_id=str(uuid4()), span_id=str(uuid4()), name=name, parent_span_id=parent_span_id, metadata=metadata or {})
            self._traces[trace.trace_id] = trace
            return trace

    def end_trace(self, trace_id: str) -> None:
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is not None:
                trace.metadata["ended"] = True

    def snapshot(self) -> list[Trace]:
        with self._lock:
            return list(self._traces.values())
