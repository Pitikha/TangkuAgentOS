from __future__ import annotations

from .interfaces import IntelligenceManagerInterface
from .models import IntelligenceGoal, IntelligencePlan, IntelligenceRequest, IntelligenceResponse, IntelligenceResult, PlanningContext


class IntelligenceManager(IntelligenceManagerInterface):
    """Core intelligence manager."""

    def register_goal(self, goal: IntelligenceGoal) -> None:
        raise NotImplementedError

    def evaluate_plan(self, plan: IntelligencePlan) -> IntelligenceResult:
        raise NotImplementedError

    def reason_over(self, context: PlanningContext) -> IntelligenceResult:
        raise NotImplementedError

    def orchestrate(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise NotImplementedError
