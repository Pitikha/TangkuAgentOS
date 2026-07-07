from __future__ import annotations

from typing import Dict

from .interfaces import ContextRegistryInterface
from .models import ContextObject
from .exceptions import ContextRegistryError


class ContextRegistry(ContextRegistryInterface):
    """Registry for storing context objects."""

    def __init__(self) -> None:
        self._contexts: Dict[str, ContextObject] = {}

    def register(self, context: ContextObject) -> None:
        self._contexts[context.context_id] = context

    def unregister(self, context_id: str) -> None:
        self._contexts.pop(context_id, None)

    def get(self, context_id: str) -> ContextObject:
        context = self._contexts.get(context_id)
        if context is None:
            raise ContextRegistryError(f"Context not found: {context_id}")
        return context

    def list(self) -> list[ContextObject]:
        return list(self._contexts.values())
