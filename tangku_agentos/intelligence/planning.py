from __future__ import annotations

from .interfaces import Planner
from .models import IntelligenceGoal, IntelligencePlan


class Planner(Planner):
    """Concrete planner abstraction."""

    def create_plan(self, goal: IntelligenceGoal) -> IntelligencePlan:
        raise NotImplementedError
