from __future__ import annotations

from threading import RLock

from .models import SecurityMetadata


class SecurityMetadataManager:
    """Store and retrieve security metadata for resources and events."""

    def __init__(self) -> None:
        self._metadata: dict[str, SecurityMetadata] = {}
        self._lock = RLock()

    def register(self, resource_id: str, metadata: SecurityMetadata) -> None:
        with self._lock:
            self._metadata[resource_id] = metadata

    def get(self, resource_id: str) -> SecurityMetadata | None:
        with self._lock:
            return self._metadata.get(resource_id)
