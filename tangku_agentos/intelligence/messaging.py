from __future__ import annotations

from .interfaces import ToolMessageBus
from .models import IntelligenceRequest


class AgentMessagingBus(ToolMessageBus):
    """Agent messaging bus for intelligence orchestration."""

    def publish(self, message: IntelligenceRequest) -> None:
        raise NotImplementedError

    def subscribe(self, channel: str) -> None:
        raise NotImplementedError
