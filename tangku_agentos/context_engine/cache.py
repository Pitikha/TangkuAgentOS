from __future__ import annotations

from threading import RLock
from typing import Dict, Optional

from .interfaces import ContextCacheInterface
from .models import ContextObject


class ContextCache(ContextCacheInterface):
    """Thread-safe in-memory cache for context objects."""

    def __init__(self) -> None:
        self._cache: Dict[str, ContextObject] = {}
        self._lock = RLock()

    def store(self, context: ContextObject) -> None:
        with self._lock:
            self._cache[context.context_id] = context

    def retrieve(self, context_id: str) -> Optional[ContextObject]:
        with self._lock:
            return self._cache.get(context_id)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
