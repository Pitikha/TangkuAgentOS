from tangku_agentos.observability import (
    AnalyticsManager,
    DiagnosticsManager,
    EventRecorder,
    HealthManager,
    LogEntry,
    LoggingManager,
    MetricsManager,
    MonitoringManager,
    ObservabilityManager,
    PerformanceManager,
    TelemetryManager,
    TimelineManager,
    TraceManager,
)


def test_observability_runtime_smoke() -> None:
    logging_manager = LoggingManager()
    metrics_manager = MetricsManager()
    trace_manager = TraceManager()
    health_manager = HealthManager()
    monitoring_manager = MonitoringManager()
    analytics_manager = AnalyticsManager()
    timeline_manager = TimelineManager()
    diagnostics_manager = DiagnosticsManager()
    event_recorder = EventRecorder()
    telemetry_manager = TelemetryManager()
    performance_manager = PerformanceManager()

    observability_manager = ObservabilityManager(
        logging_manager=logging_manager,
        metrics_manager=metrics_manager,
        trace_manager=trace_manager,
        health_manager=health_manager,
        monitoring_manager=monitoring_manager,
        analytics_manager=analytics_manager,
        timeline_manager=timeline_manager,
        diagnostics_manager=diagnostics_manager,
        event_recorder=event_recorder,
        telemetry_manager=telemetry_manager,
        performance_manager=performance_manager,
    )

    logging_manager.log(
        LogEntry(
            timestamp=1.0,
            level="INFO",
            message="agent started",
            metadata={"category": "runtime", "correlation_id": "corr-1", "agent_id": "agent-1", "session_id": "session-1"},
        )
    )
    metrics_manager.record_counter("requests", 3.0, labels={"service": "agent"})
    metrics_manager.record_gauge("queue_depth", 5.0, labels={"service": "agent"})
    metrics_manager.record_histogram("latency", 12.0, labels={"service": "agent"})
    metrics_manager.record_timer("exec_time", 1.25, labels={"service": "agent"})

    trace = trace_manager.start_trace("workflow", parent_span_id=None, metadata={"agent_id": "agent-1"})
    trace_manager.end_trace(trace.trace_id)

    health_manager.set_component_status("agent-runtime", "ready", {"latency": 12})
    health_manager.set_component_status("dependency", "degraded", {"reason": "cache warmup"})

    telemetry_manager.collect("runtime", {"status": "healthy"})
    performance_manager.record_timing("agent.exec", 0.75)

    snapshot = observability_manager.collect()

    assert snapshot["log_count"] == 1
    assert snapshot["metrics"]["requests"][0].value == 3.0
    assert snapshot["traces"] == 1
    assert snapshot["health"]["agent-runtime"]["status"] == "ready"
    assert snapshot["telemetry"][0]["source"] == "runtime"
    assert snapshot["performance"]["agent.exec"] >= 0.75

    print("observability runtime checks passed")
