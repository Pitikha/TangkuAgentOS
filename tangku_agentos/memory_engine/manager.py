from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from .configuration import MemoryConfigurationManagerImpl
from .events import MemoryEvent, MemoryEventPriority, MemoryEventType
from .exceptions import MemoryManagerError
from .interfaces import MemoryManagerInterface
from .models import MemoryMetadata, MemoryRecord, MemorySnapshot
from .registry import MemoryRegistry
from .statistics import MemoryStatisticsManagerImpl
from .store import MemoryStoreImpl


class MemoryManager(MemoryManagerInterface):
    """Persistent memory manager backed by SQLite."""

    def __init__(
        self,
        registry: MemoryRegistry | None = None,
        db_path: str | None = None,
        store: MemoryStoreImpl | None = None,
        configuration_manager: MemoryConfigurationManagerImpl | None = None,
        statistics_manager: MemoryStatisticsManagerImpl | None = None,
    ) -> None:
        self._registry = registry
        self._store = store or MemoryStoreImpl(db_path=db_path)
        self._records: Dict[str, MemoryRecord] = self._store.list_all()
        self._snapshots: Dict[str, MemorySnapshot] = self._store.list_snapshots()
        self._transaction_active = False
        self._configuration_manager = configuration_manager or MemoryConfigurationManagerImpl()
        self._statistics_manager = statistics_manager or MemoryStatisticsManagerImpl()
        self._event_handlers: list[Callable[[MemoryEvent], None]] = []
        self._refresh_statistics()

    def create_record(self, record: MemoryRecord) -> None:
        normalized = self._normalize_record(record)
        self._records[normalized.record_id] = normalized
        self._store.save(normalized)
        self._refresh_statistics()
        self._emit_event(MemoryEventType.CREATED, normalized.record_id, {"namespace": normalized.namespace})

    def read_record(self, record_id: str) -> MemoryRecord:
        record = self._records.get(record_id)
        if record is None:
            try:
                record = self._store.retrieve(record_id)
            except KeyError as exc:
                raise MemoryManagerError(f'Record not found: {record_id}') from exc
            self._records[record_id] = record
        self._emit_event(MemoryEventType.READ, record_id, {"namespace": record.namespace})
        return record

    def update_record(self, record: MemoryRecord) -> None:
        normalized = self._normalize_record(record)
        self._records[normalized.record_id] = normalized
        self._store.save(normalized)
        self._refresh_statistics()
        self._emit_event(MemoryEventType.UPDATED, normalized.record_id, {"namespace": normalized.namespace})

    def delete_record(self, record_id: str) -> None:
        self._records.pop(record_id, None)
        self._store.delete(record_id)
        self._refresh_statistics()
        self._emit_event(MemoryEventType.DELETED, record_id, {})

    def archive_record(self, record_id: str) -> None:
        record = self.read_record(record_id)
        attributes = dict(record.metadata.attributes)
        attributes['archived'] = True
        updated_metadata = MemoryMetadata(
            namespace=record.metadata.namespace,
            created_by=record.metadata.created_by,
            created_at=record.metadata.created_at,
            updated_at=self._timestamp(),
            tags=list(record.metadata.tags),
            attributes=attributes,
        )
        updated_record = MemoryRecord(
            record_id=record.record_id,
            entries=list(record.entries),
            namespace=record.namespace,
            metadata=updated_metadata,
        )
        self._records[record_id] = updated_record
        self._store.save(updated_record)
        self._refresh_statistics()
        self._emit_event(MemoryEventType.ARCHIVED, record_id, {"namespace": updated_record.namespace})

    def restore_record(self, record_id: str) -> None:
        record = self.read_record(record_id)
        attributes = dict(record.metadata.attributes)
        attributes.pop('archived', None)
        updated_metadata = MemoryMetadata(
            namespace=record.metadata.namespace,
            created_by=record.metadata.created_by,
            created_at=record.metadata.created_at,
            updated_at=self._timestamp(),
            tags=list(record.metadata.tags),
            attributes=attributes,
        )
        updated_record = MemoryRecord(
            record_id=record.record_id,
            entries=list(record.entries),
            namespace=record.namespace,
            metadata=updated_metadata,
        )
        self._records[record_id] = updated_record
        self._store.save(updated_record)
        self._refresh_statistics()
        self._emit_event(MemoryEventType.RESTORED, record_id, {"namespace": updated_record.namespace})

    def snapshot_record(self, record_id: str) -> MemorySnapshot:
        record = self.read_record(record_id)
        snapshot = MemorySnapshot(snapshot_id=f'{record_id}-snapshot', record=record)
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._store.save_snapshot(snapshot)
        self._emit_event(MemoryEventType.SYNCHRONIZED, record_id, {"snapshot_id": snapshot.snapshot_id})
        return snapshot

    def begin_transaction(self) -> None:
        self._transaction_active = True

    def commit_transaction(self) -> None:
        self._transaction_active = False

    def rollback_transaction(self) -> None:
        self._transaction_active = False

    def register_event_handler(self, handler: Callable[[MemoryEvent], None]) -> None:
        self._event_handlers.append(handler)

    def list_records(self) -> list[MemoryRecord]:
        return list(self._records.values())

    def store(self, record_id: str, record: MemoryRecord) -> None:
        normalized = self._normalize_record(
            MemoryRecord(
                record_id=record_id,
                entries=list(record.entries),
                namespace=record.namespace or record.metadata.namespace or 'default',
                metadata=record.metadata,
            )
        )
        self._records[normalized.record_id] = normalized
        self._store.save(normalized)
        self._refresh_statistics()

    def list_with_filter(self, namespace: str | None = None) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        for record in self._records.values():
            if namespace is None:
                records.append(record)
                continue
            if record.namespace == namespace or record.metadata.namespace == namespace or namespace in record.metadata.tags:
                records.append(record)
        return records

    def _normalize_record(self, record: MemoryRecord) -> MemoryRecord:
        metadata = record.metadata
        namespace = record.namespace or metadata.namespace or 'default'
        normalized_metadata = MemoryMetadata(
            namespace=namespace,
            created_by=metadata.created_by or 'system',
            created_at=metadata.created_at or self._timestamp(),
            updated_at=self._timestamp(),
            tags=list(metadata.tags),
            attributes=dict(metadata.attributes),
        )
        return MemoryRecord(record_id=record.record_id, entries=list(record.entries), namespace=namespace, metadata=normalized_metadata)

    def _refresh_statistics(self) -> None:
        namespace_counter: Counter[str] = Counter(record.namespace or 'default' for record in self._records.values())
        total_entries = sum(len(record.entries) for record in self._records.values())
        self._statistics_manager.update(
            total_records=len(self._records),
            total_entries=total_entries,
            namespaces=dict(namespace_counter),
        )

    def _emit_event(self, event_type: MemoryEventType, record_id: str, payload: dict[str, Any]) -> None:
        event = MemoryEvent(
            event_type=event_type,
            memory_id=record_id,
            payload=payload,
            priority=MemoryEventPriority.MEDIUM,
            metadata={"namespace": payload.get("namespace", "default")},
        )
        for handler in self._event_handlers:
            handler(event)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
