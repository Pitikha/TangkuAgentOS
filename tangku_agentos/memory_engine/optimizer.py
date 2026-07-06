from __future__ import annotations

from .interfaces import MemoryOptimizer
from .models import MemoryCollection


class MemoryOptimizerImpl(MemoryOptimizer):
    """Skeleton memory optimizer."""

    def optimize(self, collection: MemoryCollection) -> MemoryCollection:
        return collection
