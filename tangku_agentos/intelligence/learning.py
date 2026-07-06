from __future__ import annotations

from .interfaces import LearningManager
from .models import LearningSession, ReflectionReport, IntelligenceGoal


class LearningManager(LearningManager):
    """Concrete learning manager."""

    def record(self, session: LearningSession) -> None:
        raise NotImplementedError

    def summarize(self, goal: IntelligenceGoal) -> ReflectionReport:
        raise NotImplementedError
