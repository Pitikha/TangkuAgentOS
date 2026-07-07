from __future__ import annotations

from threading import RLock
from time import time

from .interfaces import AuditManager
from .models import AuditRecord


class AuditManager(AuditManager):
    """Audit manager architecture for security events and decisions."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self._lock = RLock()

    def record(self, audit_record: AuditRecord) -> None:
        with self._lock:
            self._records.append(audit_record)

    def query(self, filters: dict[str, str]) -> list[AuditRecord]:
        with self._lock:
            return [record for record in self._records if all(str(getattr(record, key, '')) == value for key, value in filters.items())]

    def record_event(self, event: str, identity: str, metadata: dict[str, object] | None = None) -> None:
        self.record(AuditRecord(record_id=str(time()), event=event, identity=identity, timestamp=time(), metadata=metadata or {}))
