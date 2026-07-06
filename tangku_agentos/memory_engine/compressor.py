from __future__ import annotations

from .interfaces import MemoryCompressor
from .models import MemoryRecord


class MemoryCompressorImpl(MemoryCompressor):
    """Skeleton memory compressor."""

    def compress(self, record: MemoryRecord) -> MemoryRecord:
        return record
