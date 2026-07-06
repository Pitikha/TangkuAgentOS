from __future__ import annotations

from threading import RLock

from .interfaces import MetricsManager
from .models import Metric


class MetricsManager(MetricsManager):
    """In-process metrics manager with counters, gauges, histograms, and timers."""

    def __init__(self) -> None:
        self._metrics: dict[str, list[Metric]] = {}
        self._lock = RLock()

    def record_metric(self, metric: Metric) -> None:
        with self._lock:
            self._metrics.setdefault(metric.name, []).append(metric)

    def get_metrics(self, name: str) -> list[Metric]:
        with self._lock:
            return list(self._metrics.get(name, []))

    def record_counter(self, name: str, value: float, *, labels: dict[str, str] | None = None, metadata: dict[str, object] | None = None) -> None:
        self.record_metric(Metric(name=name, value=value, labels=labels or {}, metadata=metadata or {}))

    def record_gauge(self, name: str, value: float, *, labels: dict[str, str] | None = None, metadata: dict[str, object] | None = None) -> None:
        self.record_metric(Metric(name=name, value=value, labels=labels or {}, metadata=metadata or {}))

    def record_histogram(self, name: str, value: float, *, labels: dict[str, str] | None = None, metadata: dict[str, object] | None = None) -> None:
        self.record_metric(Metric(name=name, value=value, labels=labels or {}, metadata=metadata or {}))

    def record_timer(self, name: str, value: float, *, labels: dict[str, str] | None = None, metadata: dict[str, object] | None = None) -> None:
        self.record_metric(Metric(name=name, value=value, labels=labels or {}, metadata=metadata or {}))

    def snapshot(self) -> dict[str, list[Metric]]:
        with self._lock:
            return {key: list(values) for key, values in self._metrics.items()}
