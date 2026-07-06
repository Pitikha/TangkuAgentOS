from __future__ import annotations

from .interfaces import ReasoningManager
from .models import IntelligencePlan, IntelligenceResult


class ReasoningManager(ReasoningManager):
    """Concrete reasoning manager."""

    def infer(self, plan: IntelligencePlan) -> IntelligenceResult:
        raise NotImplementedError
