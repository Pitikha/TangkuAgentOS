from __future__ import annotations

from typing import Any

from .interfaces import TriggerManagerInterface
from .models import TriggerContext, TriggerResult
from .registry import TriggerRegistry


class TriggerManager(TriggerManagerInterface):
    """Manager for registering and dispatching triggers."""

    def __init__(self, registry: TriggerRegistry) -> None:
        self._registry = registry

    def register_trigger(self, trigger_type: str, handler: Any) -> None:
        self._registry.register(trigger_type, handler)

    def trigger(self, trigger_type: str, context: TriggerContext) -> TriggerResult:
        handler = self._registry.resolve(trigger_type)
        return handler.trigger(context)
