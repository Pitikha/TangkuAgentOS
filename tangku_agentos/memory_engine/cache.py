from __future__ import annotations

from typing import Dict, Optional

from .interfaces import MemoryCache
from .models import MemoryRecord


class MemoryCacheImpl(MemoryCache):
    """Skeleton memory cache."""

    def __init__(self) -> None:
        self._cache: Dict[str, MemoryRecord] = {}

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._cache.get(record_id)

    def put(self, record: MemoryRecord) -> None:
        self._cache[record.record_id] = record
