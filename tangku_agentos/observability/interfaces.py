from __future__ import annotations

from abc import ABC, abstractmethod

from .models import DiagnosticReport, EventTimeline, HealthReport, LogEntry, Metric, PerformanceReport, Trace


class LoggingManager(ABC):
    """Interface for logging management."""

    @abstractmethod
    def log(self, entry: LogEntry) -> None:
        ...


class MetricsManager(ABC):
    """Interface for metrics management."""

    @abstractmethod
    def record_metric(self, metric: Metric) -> None:
        ...

    @abstractmethod
    def get_metrics(self, name: str) -> list[Metric]:
        ...


class TraceManager(ABC):
    """Interface for tracing."""

    @abstractmethod
    def start_trace(self, trace: Trace) -> None:
        ...

    @abstractmethod
    def end_trace(self, trace_id: str) -> None:
        ...


class HealthManager(ABC):
    """Interface for health monitoring."""

    @abstractmethod
    def check_health(self) -> HealthReport:
        ...


class MonitoringManager(ABC):
    """Interface for monitoring."""

    @abstractmethod
    def monitor(self) -> EventTimeline:
        ...


class AnalyticsManager(ABC):
    """Interface for analytics."""

    @abstractmethod
    def analyze(self, data: dict[str, str]) -> PerformanceReport:
        ...


class EventRecorder(ABC):
    """Interface for event recording."""

    @abstractmethod
    def record(self, event: EventTimeline) -> None:
        ...


class TimelineManager(ABC):
    """Interface for timeline management."""

    @abstractmethod
    def add_event(self, event: EventTimeline) -> None:
        ...


class DiagnosticsManager(ABC):
    """Interface for diagnostics."""

    @abstractmethod
    def diagnose(self) -> DiagnosticReport:
        ...
