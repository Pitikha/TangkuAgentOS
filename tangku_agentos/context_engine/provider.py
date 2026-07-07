from __future__ import annotations

from .cache import ContextCache
from .interfaces import ContextProviderInterface
from .models import ContextObject
from .registry import ContextRegistry


class ContextProvider(ContextProviderInterface):
    """Provide context objects from the registry and cache."""

    def __init__(self, registry: ContextRegistry | None = None, cache: ContextCache | None = None) -> None:
        self._registry = registry or ContextRegistry()
        self._cache = cache or ContextCache()

    def provide(self, context_id: str) -> ContextObject:
        cached = self._cache.retrieve(context_id)
        if cached is not None:
            return cached
        context = self._registry.get(context_id)
        self._cache.store(context)
        return context
