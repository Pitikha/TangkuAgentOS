from __future__ import annotations

from .interfaces import MemoryMetadataManager
from .models import MemoryMetadata


class MemoryMetadataManagerImpl(MemoryMetadataManager):
    """Attach or replace metadata information for a record."""

    def __init__(self) -> None:
        self._metadata: dict[str, MemoryMetadata] = {}

    def update_metadata(self, record_id: str, metadata: MemoryMetadata) -> None:
        self._metadata[record_id] = metadata
