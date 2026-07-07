from __future__ import annotations

from .interfaces import MemoryStatisticsManager
from .models import MemoryStatistics


class MemoryStatisticsManagerImpl(MemoryStatisticsManager):
    """Collect basic statistics about the memory store."""

    def __init__(self) -> None:
        self._statistics = MemoryStatistics()

    def statistics(self) -> MemoryStatistics:
        return self._statistics

    def update(self, *, total_records: int | None = None, total_entries: int | None = None, namespaces: dict[str, int] | None = None) -> None:
        if total_records is not None:
            self._statistics.total_records = total_records
        if total_entries is not None:
            self._statistics.total_entries = total_entries
        if namespaces is not None:
            self._statistics.namespaces = namespaces
