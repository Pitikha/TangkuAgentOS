from __future__ import annotations

from .interfaces import Orchestrator
from .models import IntelligenceTask


class Orchestrator(Orchestrator):
    """Concrete orchestration manager."""

    def orchestrate(self, tasks: list[IntelligenceTask]) -> list[IntelligenceTask]:
        raise NotImplementedError
