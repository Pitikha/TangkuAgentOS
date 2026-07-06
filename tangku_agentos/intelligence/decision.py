from __future__ import annotations

from .interfaces import DecisionManager
from .models import IntelligenceRequest, IntelligenceResponse


class DecisionManager(DecisionManager):
    """Concrete decision manager."""

    def decide(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise NotImplementedError
