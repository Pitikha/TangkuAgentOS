from pathlib import Path

from tangku_agentos.memory_engine import (
    MemoryConfiguration,
    MemoryManager,
    MemoryMetadata,
    MemoryRecord,
    MemoryRegistry,
    MemoryType,
)


def test_memory_manager_persists_records_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "memory.sqlite3"
    registry = MemoryRegistry()
    registry.register("project", MemoryConfiguration(default_memory_type=MemoryType.PROJECT, max_entries=32))

    manager = MemoryManager(registry=registry, db_path=str(db_path))
    record = MemoryRecord(
        record_id="rec-1",
        namespace="project",
        metadata=MemoryMetadata(namespace="project", created_by="tester", tags=["pytest"]),
    )
    manager.create_record(record)

    reloaded = MemoryManager(registry=registry, db_path=str(db_path))
    restored = reloaded.read_record("rec-1")

    assert restored.record_id == "rec-1"
    assert restored.namespace == "project"
    assert restored.metadata.tags == ["pytest"]


def test_memory_manager_supports_archive_restore_and_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "memory.sqlite3"
    registry = MemoryRegistry()
    registry.register("conversation", MemoryConfiguration(default_memory_type=MemoryType.CONVERSATION, max_entries=16))

    manager = MemoryManager(registry=registry, db_path=str(db_path))
    record = MemoryRecord(
        record_id="rec-2",
        namespace="conversation",
        metadata=MemoryMetadata(namespace="conversation", created_by="tester"),
    )
    manager.create_record(record)

    manager.archive_record("rec-2")
    archived = manager.read_record("rec-2")
    assert archived.metadata.attributes["archived"] is True

    manager.restore_record("rec-2")
    restored = manager.read_record("rec-2")
    assert "archived" not in restored.metadata.attributes

    snapshot = manager.snapshot_record("rec-2")
    assert snapshot.record.record_id == "rec-2"
    assert snapshot.snapshot_id.endswith("-snapshot")
