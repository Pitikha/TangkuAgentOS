from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class LogEntry:
    timestamp: float
    level: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LogMetadata:
    category: str = "runtime"
    correlation_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class LogContext:
    context_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LogSession:
    session_id: str
    entries: List[LogEntry] = field(default_factory=list)


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Trace:
    trace_id: str
    span_id: str
    name: str
    parent_span_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceMetadata:
    agent_id: str | None = None
    workflow_id: str | None = None
    tool_id: str | None = None


@dataclass(frozen=True)
class SpanContext:
    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventTimeline:
    timeline_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthReport:
    overall_status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PerformanceReport:
    report_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosticReport:
    report_id: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TelemetryRecord:
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


@dataclass(frozen=True)
class TelemetrySession:
    session_id: str
    records: List[TelemetryRecord] = field(default_factory=list)
