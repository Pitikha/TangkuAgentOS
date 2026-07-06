from __future__ import annotations

from .interfaces import AnalyticsManager
from .models import PerformanceReport


class AnalyticsManager(AnalyticsManager):
    """Lightweight analytics manager for in-process performance summaries."""

    def analyze(self, data: dict[str, str]) -> PerformanceReport:
        return PerformanceReport(report_id="analytics", metrics=data, metadata={"source": "internal"})
