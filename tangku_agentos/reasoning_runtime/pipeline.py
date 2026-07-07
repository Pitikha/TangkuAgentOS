from __future__ import annotations

from threading import RLock

from .models import ReasoningContext, ReasoningMode, ReasoningStep, ReasoningTrace


class ReasoningPipeline:
    """Runtime abstraction for reasoning execution pipelines."""

    def __init__(self) -> None:
        self._traces: dict[str, ReasoningTrace] = {}
        self._lock = RLock()

    def execute(self, context: ReasoningContext, steps: list[ReasoningStep]) -> ReasoningTrace:
        trace = ReasoningTrace(trace_id=f"trace-{context.context_id}", steps=tuple(steps), metadata={"mode": context.mode.value})
        with self._lock:
            self._traces[trace.trace_id] = trace
        return trace

    def get_trace(self, trace_id: str) -> ReasoningTrace | None:
        with self._lock:
            return self._traces.get(trace_id)
