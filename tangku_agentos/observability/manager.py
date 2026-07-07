from __future__ import annotations

from .interfaces import DiagnosticsManager, HealthManager, LoggingManager, MetricsManager, MonitoringManager, TraceManager, TimelineManager, EventRecorder


class ObservabilityManager:
    """Aggregates observability components into a single runtime snapshot."""

    def __init__(
        self,
        logging_manager: LoggingManager,
        metrics_manager: MetricsManager,
        trace_manager: TraceManager,
        health_manager: HealthManager,
        monitoring_manager: MonitoringManager,
        analytics_manager: "AnalyticsManager",
        timeline_manager: TimelineManager,
        diagnostics_manager: DiagnosticsManager,
        event_recorder: EventRecorder,
        telemetry_manager: object | None = None,
        performance_manager: object | None = None,
    ) -> None:
        self.logging_manager = logging_manager
        self.metrics_manager = metrics_manager
        self.trace_manager = trace_manager
        self.health_manager = health_manager
        self.monitoring_manager = monitoring_manager
        self.analytics_manager = analytics_manager
        self.timeline_manager = timeline_manager
        self.diagnostics_manager = diagnostics_manager
        self.event_recorder = event_recorder
        self.telemetry_manager = telemetry_manager
        self.performance_manager = performance_manager

    def collect(self) -> dict[str, object]:
        log_snapshot = []
        if hasattr(self.logging_manager, "snapshot"):
            log_snapshot = self.logging_manager.snapshot()
        metrics_snapshot = {}
        if hasattr(self.metrics_manager, "snapshot"):
            metrics_snapshot = self.metrics_manager.snapshot()
        trace_snapshot = []
        if hasattr(self.trace_manager, "snapshot"):
            trace_snapshot = self.trace_manager.snapshot()
        health_snapshot = {}
        if hasattr(self.health_manager, "snapshot"):
            health_snapshot = self.health_manager.snapshot()
        telemetry_snapshot = []
        if self.telemetry_manager is not None and hasattr(self.telemetry_manager, "snapshot"):
            telemetry_snapshot = self.telemetry_manager.snapshot()
        performance_snapshot = {}
        if self.performance_manager is not None and hasattr(self.performance_manager, "snapshot"):
            performance_snapshot = self.performance_manager.snapshot()
        return {
            "log_count": len(log_snapshot),
            "logs": log_snapshot,
            "metrics": metrics_snapshot,
            "traces": len(trace_snapshot),
            "health": health_snapshot,
            "telemetry": telemetry_snapshot,
            "performance": performance_snapshot,
        }
