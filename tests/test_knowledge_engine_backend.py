from __future__ import annotations

from pathlib import Path

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.knowledge_engine import (
    KnowledgeConfiguration,
    KnowledgeConfigurationManager,
    KnowledgeGraphManager,
    KnowledgeManager,
    KnowledgeSearchManager,
    KnowledgeStatisticsManager,
    KnowledgeSource,
    KnowledgeSourceType,
)
from tangku_agentos.knowledge_engine.models import KnowledgeEntity


class DummyPermissionManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def has_permission(self, role_id: str, permission_id: str) -> bool:
        self.calls.append((role_id, permission_id))
        return True


class DummyAuditManager:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    def record_event(self, event: str, identity: str, metadata: dict | None = None) -> None:
        self.events.append((event, identity, metadata or {}))


class DummySecurityManager:
    def __init__(self) -> None:
        self.permission_manager = DummyPermissionManager()
        self.audit_manager = DummyAuditManager()

    def get_permission_manager(self) -> DummyPermissionManager:
        return self.permission_manager

    def get_audit_manager(self) -> DummyAuditManager:
        return self.audit_manager


class DummyObservabilityManager:
    def __init__(self) -> None:
        self.records: list[dict] = []

    @property
    def event_recorder(self) -> object:
        class Recorder:
            def __init__(self, owner: DummyObservabilityManager) -> None:
                self.owner = owner

            def record(self, event: object) -> None:
                self.owner.records.append({"event": event})

        return Recorder(self)


def test_knowledge_backend_entity_relationship_search_and_persistence(tmp_path: Path) -> None:
    db_path = tmp_path / "knowledge.sqlite"
    security_manager = DummySecurityManager()
    event_bus = EventBus()
    events: list[tuple[str, dict]] = []
    event_bus.subscribe("knowledge.entity.created", lambda name, payload: events.append((name, payload)))

    manager = KnowledgeManager(
        db_path=str(db_path),
        security_manager=security_manager,
        event_bus=event_bus,
        observability_manager=DummyObservabilityManager(),
    )

    entity = manager.create_entity(
        entity_type="concept",
        name="Architecture",
        description="System design",
        tags=["design"],
        metadata={"workspace": "alpha"},
    )
    assert entity.entity_id
    assert entity.name == "Architecture"

    updated = manager.update_entity(entity.entity_id, name="Architecture v2", description="Updated")
    assert updated.version == 2
    assert updated.description == "Updated"

    source = KnowledgeSource(source_id="src-1", source_type=KnowledgeSourceType.TEXT, uri="https://example.test")
    manager.register_source(source)

    manager.create_relationship(
        source_entity_id=entity.entity_id,
        target_entity_id="entity-2",
        relationship_type="related_to",
        metadata={"confidence": 0.9},
    )

    graph = manager.graph_manager
    assert graph.outgoing_relationships(entity.entity_id)[0].relationship_type == "related_to"
    assert graph.traverse(entity.entity_id, max_depth=1)[0].target_entity_id == "entity-2"

    search = manager.search_entities("Architecture")
    assert any(item.item_id == entity.entity_id for item in search.documents)

    manager.begin_session("session-1")
    manager.end_session("session-1")

    stats = manager.statistics()
    assert stats["entity_count"] >= 2
    assert stats["relationship_count"] >= 1

    health = manager.health()
    assert health["memory_connectivity"] is True

    manager2 = KnowledgeManager(db_path=str(db_path), security_manager=security_manager, event_bus=event_bus)
    restored = manager2.get_entity(entity.entity_id)
    assert restored.name == "Architecture v2"
    assert manager2.graph_manager.outgoing_relationships(entity.entity_id)[0].relationship_type == "related_to"
    assert events


def test_knowledge_search_config_and_statistics() -> None:
    search_manager = KnowledgeSearchManager()
    search_manager.register_document(KnowledgeEntity(entity_id="doc-1", name="Maps", entity_type="document"))
    result = search_manager.search("Maps")
    assert result.documents[0].item_id == "doc-1"

    config_manager = KnowledgeConfigurationManager()
    config_manager.set_configuration(
        "default",
        KnowledgeConfiguration(
            metadata={"cache_size": 16, "search_limit": 3},
            search_types=["semantic"],
        ),
    )
    config = config_manager.get_configuration("default")
    assert config.metadata["cache_size"] == 16

    stats_manager = KnowledgeStatisticsManager()
    stats_manager.record_search(2)
    stats_manager.record_update(1)
    stats_manager.record_cache_hit(3)
    stats_manager.record_cache_miss(1)
    assert stats_manager.statistics()["search_count"] == 2
    assert stats_manager.statistics()["update_count"] == 1
    assert stats_manager.statistics()["cache_hits"] == 3
