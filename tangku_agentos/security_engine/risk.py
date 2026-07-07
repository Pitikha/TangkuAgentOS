from __future__ import annotations

from .interfaces import RiskAssessmentManager
from .models import RiskLevel


class RiskAssessmentManager(RiskAssessmentManager):
    """Risk assessment manager architecture."""

    def assess(self, context: dict[str, str]) -> RiskLevel:
        score = context.get("risk_score", "0")
        try:
            numeric = float(score)
        except ValueError:
            numeric = 0.0
        if numeric >= 0.75:
            return RiskLevel.CRITICAL
        if numeric >= 0.5:
            return RiskLevel.HIGH
        if numeric >= 0.25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
