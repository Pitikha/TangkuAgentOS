from __future__ import annotations

from .cache import ContextCache
from .exceptions import ContextResolverError
from .interfaces import ContextResolverInterface
from .models import ContextObject
from .registry import ContextRegistry


class ContextResolver(ContextResolverInterface):
    """Resolve context references using the registry and cache."""

    def __init__(self, registry: ContextRegistry | None = None, cache: ContextCache | None = None) -> None:
        self._registry = registry or ContextRegistry()
        self._cache = cache or ContextCache()

    def resolve(self, reference_id: str) -> ContextObject:
        cached = self._cache.retrieve(reference_id)
        if cached is not None:
            return cached
        try:
            context = self._registry.get(reference_id)
        except Exception as error:
            raise ContextResolverError(str(error)) from error
        self._cache.store(context)
        return context
