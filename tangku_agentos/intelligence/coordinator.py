from __future__ import annotations

from typing import Iterable

from .interfaces import AgentCoordinator
from .models import IntelligenceTask


class IntelligenceCoordinator(AgentCoordinator):
    """Concrete implementation of multi-agent coordination."""

    def coordinate(self, tasks: Iterable[IntelligenceTask]) -> list[IntelligenceTask]:
        return list(tasks)
