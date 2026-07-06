from __future__ import annotations

from .interfaces import IntelligenceRouter
from .models import IntelligenceRequest, IntelligenceResponse


class IntelligenceRouter(IntelligenceRouter):
    """Concrete router for intelligence requests."""

    def route(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise NotImplementedError
