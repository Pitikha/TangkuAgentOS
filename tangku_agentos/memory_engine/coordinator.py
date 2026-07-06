from __future__ import annotations

from .interfaces import MemoryCoordinator
from .models import MemoryCollection, MemoryRecord, MemoryState


class MemoryCoordinatorImpl(MemoryCoordinator):
    """Coordinate records in a collection by ensuring each record has a namespace."""

    def coordinate(self, collection: MemoryCollection) -> None:
        for record in collection.records:
            if not record.namespace:
                record.namespace = collection.namespace
            record.metadata.attributes.setdefault("coordinated", True)
            for entry in record.entries:
                entry.metadata.attributes.setdefault("coordinated", True)
