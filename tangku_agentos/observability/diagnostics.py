from __future__ import annotations

from .interfaces import DiagnosticsManager
from .models import DiagnosticReport


class DiagnosticsManager(DiagnosticsManager):
    """Diagnostics manager with simple report generation."""

    def diagnose(self) -> DiagnosticReport:
        return DiagnosticReport(report_id="diagnostics", diagnostics={"status": "ok"}, metadata={"source": "internal"})
