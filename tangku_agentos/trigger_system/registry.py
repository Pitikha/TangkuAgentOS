from __future__ import annotations

from typing import Any, Dict

from .interfaces import TriggerRegistryInterface


class TriggerRegistry(TriggerRegistryInterface):
    """Registry for trigger handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Any] = {}

    def register(self, trigger_type: str, handler: Any) -> None:
        self._handlers[trigger_type] = handler

    def resolve(self, trigger_type: str) -> Any:
        return self._handlers[trigger_type]

    def list_registered(self) -> list[str]:
        return list(self._handlers.keys())
