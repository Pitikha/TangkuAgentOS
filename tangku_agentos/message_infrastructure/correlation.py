"""
Correlation ID and Tracing Infrastructure
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trace:
    """Execution trace for a correlated set of messages."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, failed
    message_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message_id: str) -> None:
        """Add message to trace."""
        self.message_ids.append(message_id)

    def complete(self, status: str = "completed") -> None:
        """Mark trace as complete."""
        self.status = status
        self.end_time = datetime.utcnow()

    def duration_ms(self) -> float:
        """Get trace duration in milliseconds."""
        end = self.end_time or datetime.utcnow()
        delta = end - self.start_time
        return delta.total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "duration_ms": self.duration_ms(),
            "message_count": len(self.message_ids),
            "metadata": self.metadata,
        }


class CorrelationManager:
    """
    Manages correlation IDs and execution traces for message tracking.
    """

    def __init__(self, max_traces: int = 10000):
        self.traces: Dict[str, Trace] = {}
        self.max_traces = max_traces
        self.correlation_mapping: Dict[str, str] = {}  # correlation_id -> trace_id

    def start_trace(
        self,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trace:
        """
        Start a new execution trace.

        Returns:
            New trace object
        """
        trace = Trace(source=source)
        if metadata:
            trace.metadata = metadata

        self.traces[trace.trace_id] = trace
        self.correlation_mapping[trace.correlation_id] = trace.trace_id

        if len(self.traces) > self.max_traces:
            # Remove oldest completed trace
            self._cleanup_oldest()

        logger.debug(
            f"Trace started: {trace.trace_id} (correlation: {trace.correlation_id})"
        )
        return trace

    def add_message_to_trace(
        self, trace_id: str, message_id: str
    ) -> Optional[Trace]:
        """Add message to trace."""
        trace = self.traces.get(trace_id)
        if trace:
            trace.add_message(message_id)
            return trace
        return None

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID."""
        return self.traces.get(trace_id)

    def get_trace_by_correlation(
        self, correlation_id: str
    ) -> Optional[Trace]:
        """Get trace by correlation ID."""
        trace_id = self.correlation_mapping.get(correlation_id)
        if trace_id:
            return self.traces.get(trace_id)
        return None

    def complete_trace(self, trace_id: str, status: str = "completed") -> bool:
        """Mark trace as complete."""
        trace = self.traces.get(trace_id)
        if trace:
            trace.complete(status)
            return True
        return False

    def get_active_traces(self) -> List[Trace]:
        """Get all active traces."""
        return [t for t in self.traces.values() if t.status == "active"]

    def get_trace_stats(self) -> Dict[str, Any]:
        """Get trace statistics."""
        traces = list(self.traces.values())
        active = [t for t in traces if t.status == "active"]
        completed = [t for t in traces if t.status == "completed"]
        failed = [t for t in traces if t.status == "failed"]

        avg_duration = (
            sum(t.duration_ms() for t in completed) / len(completed)
            if completed
            else 0
        )

        return {
            "total_traces": len(traces),
            "active_traces": len(active),
            "completed_traces": len(completed),
            "failed_traces": len(failed),
            "average_duration_ms": avg_duration,
        }

    def _cleanup_oldest(self) -> None:
        """Remove oldest trace to maintain size limit."""
        if not self.traces:
            return

        # Find oldest completed trace
        oldest = None
        for trace in self.traces.values():
            if trace.status != "active":
                if oldest is None or trace.end_time < oldest.end_time:
                    oldest = trace

        # If no completed trace, remove oldest trace
        if oldest is None:
            oldest = min(self.traces.values(), key=lambda t: t.start_time)

        trace_id = oldest.trace_id
        correlation_id = oldest.correlation_id

        del self.traces[trace_id]
        if correlation_id in self.correlation_mapping:
            del self.correlation_mapping[correlation_id]

        logger.debug(f"Trace cleanup: {trace_id}")

    def clear_completed(self) -> int:
        """Clear completed traces. Returns count cleared."""
        trace_ids_to_remove = [
            tid
            for tid, t in self.traces.items()
            if t.status in ("completed", "failed")
        ]

        for tid in trace_ids_to_remove:
            trace = self.traces.pop(tid)
            if trace.correlation_id in self.correlation_mapping:
                del self.correlation_mapping[trace.correlation_id]

        return len(trace_ids_to_remove)
