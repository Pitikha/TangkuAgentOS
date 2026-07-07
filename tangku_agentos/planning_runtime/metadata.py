from __future__ import annotations

from threading import RLock

from .models import PlanningMetadata


class PlanningMetadataManager:
    """Manage planning metadata."""

    def __init__(self) -> None:
        self._metadata: dict[str, PlanningMetadata] = {}
        self._lock = RLock()

    def set_metadata(self, plan_id: str, metadata: PlanningMetadata) -> None:
        with self._lock:
            self._metadata[plan_id] = metadata

    def get_metadata(self, plan_id: str) -> PlanningMetadata | None:
        with self._lock:
            return self._metadata.get(plan_id)
