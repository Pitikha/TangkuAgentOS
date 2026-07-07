from __future__ import annotations

from .interfaces import MemoryVersionManager
from .models import MemoryRecord, MemorySnapshot


class MemoryVersionManagerImpl(MemoryVersionManager):
    """Create version snapshots for a record."""

    def __init__(self) -> None:
        self._versions: dict[str, MemorySnapshot] = {}

    def create_version(self, record: MemoryRecord) -> MemorySnapshot:
        snapshot = MemorySnapshot(snapshot_id=f'{record.record_id}-version', record=record)
        self._versions[snapshot.snapshot_id] = snapshot
        return snapshot
