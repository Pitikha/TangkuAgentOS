from __future__ import annotations

from .exceptions import ContextSnapshotError
from .interfaces import ContextSnapshotManagerInterface
from .models import ContextObject


class ContextSnapshotManager(ContextSnapshotManagerInterface):
    """Persist and retrieve versioned context snapshots."""

    def __init__(self) -> None:
        self._snapshots: dict[str, ContextObject] = {}

    def snapshot(self, context: ContextObject) -> None:
        self._snapshots[context.context_id] = context

    def get_snapshot(self, context_id: str) -> ContextObject:
        snapshot = self._snapshots.get(context_id)
        if snapshot is None:
            raise ContextSnapshotError(f"Snapshot not found: {context_id}")
        return snapshot

    def clear(self) -> None:
        self._snapshots.clear()
