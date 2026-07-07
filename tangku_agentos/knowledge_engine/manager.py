from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict
from uuid import uuid4

from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .configuration import KnowledgeConfigurationManager
from .exceptions import KnowledgeManagerError
from .graph_manager import KnowledgeGraphManager
from .interfaces import KnowledgeManagerInterface
from .models import KnowledgeConfiguration, KnowledgeDocument, KnowledgeEntity, KnowledgeMetadata, KnowledgeRelationship, KnowledgeSession, KnowledgeSource, KnowledgeSourceType
from .registry import KnowledgeRegistry
from .search import KnowledgeSearchManager
from .source_manager import KnowledgeSourceManager
from .statistics import KnowledgeStatisticsManager


class KnowledgeManager(KnowledgeManagerInterface):
    """Persistent knowledge manager backed by the Memory Engine."""

    def __init__(
        self,
        registry: KnowledgeRegistry | None = None,
        db_path: str | None = None,
        store: Any | None = None,
        configuration_manager: KnowledgeConfigurationManager | None = None,
        statistics_manager: KnowledgeStatisticsManager | None = None,
        security_manager: Any | None = None,
        event_bus: Any | None = None,
        observability_manager: Any | None = None,
    ) -> None:
        self._registry = registry or KnowledgeRegistry()
        self._memory_manager = MemoryManager(db_path=db_path, store=store)
        self._configuration_manager = configuration_manager or KnowledgeConfigurationManager()
        self._statistics_manager = statistics_manager or KnowledgeStatisticsManager()
        self._security_manager = security_manager
        self._event_bus = event_bus
        self._observability_manager = observability_manager
        self._graph_manager = KnowledgeGraphManager()
        self._search_manager = KnowledgeSearchManager()
        self._source_manager = KnowledgeSourceManager()
        self._entities: Dict[str, KnowledgeEntity] = {}
        self._relationships: Dict[str, KnowledgeRelationship] = {}
        self._sessions: Dict[str, KnowledgeSession] = {}
        self._lock = RLock()
        self._state = "initialized"
        self._kernel: Any | None = None
        self._hydrate_from_memory()

    @property
    def graph_manager(self) -> KnowledgeGraphManager:
        return self._graph_manager

    def initialize(self) -> None:
        self._state = "initialized"
        self._emit_event("knowledge.initialized", {"state": self._state})

    def start(self) -> None:
        self._state = "running"
        self._emit_event("knowledge.started", {"state": self._state})

    def pause(self) -> None:
        self._state = "paused"
        self._emit_event("knowledge.paused", {"state": self._state})

    def resume(self) -> None:
        self._state = "running"
        self._emit_event("knowledge.resumed", {"state": self._state})

    def stop(self) -> None:
        self._state = "stopped"
        self._emit_event("knowledge.stopped", {"state": self._state})

    def shutdown(self) -> None:
        self._state = "shutdown"
        self._emit_event("knowledge.shutdown", {"state": self._state})

    def cleanup(self) -> None:
        self._sessions.clear()
        self._emit_event("knowledge.cleaned", {"state": self._state})

    def register_document(self, document: KnowledgeDocument) -> None:
        self._ensure_permission("knowledge:create")
        self._audit("knowledge.document.registered", {"document_id": document.document_id})
        self._entities[document.document_id] = KnowledgeEntity(
            entity_id=document.document_id,
            name=document.metadata.title or document.document_id,
            description=document.metadata.title or '',
            entity_type='document',
            metadata=dict(document.content),
            tags=list(document.metadata.tags),
            created_at=document.metadata.created_at or self._timestamp(),
            updated_at=document.metadata.updated_at or self._timestamp(),
            version=1,
            confidence_score=1.0,
            source_references=[document.source.source_id] if document.source.source_id else [],
        )
        self._persist_entity(self._entities[document.document_id])
        self._search_manager.register_document(self._entities[document.document_id])
        self._statistics_manager.record_update(1)
        self._emit_event("knowledge.entity.created", {"entity_id": document.document_id, "entity_type": "document"})

    def get_document(self, document_id: str) -> KnowledgeDocument:
        entity = self.get_entity(document_id)
        return KnowledgeDocument(
            item_id=entity.entity_id,
            document_id=entity.entity_id,
            content={"name": entity.name, "entity_type": entity.entity_type, **entity.metadata},
            metadata=KnowledgeMetadata(title=entity.name, source_type=KnowledgeSourceType.TEXT, tags=entity.tags),
        )

    def list_documents(self) -> list[KnowledgeDocument]:
        return [self.get_document(entity.entity_id) for entity in self._entities.values() if entity.entity_type == 'document']

    def register_source(self, source: KnowledgeSource) -> None:
        self._ensure_permission("knowledge:create")
        self._audit("knowledge.source.registered", {"source_id": source.source_id})
        self._source_manager.register_source(source)
        self._persist_source(source)
        self._emit_event("knowledge.source.created", {"source_id": source.source_id})

    def create_entity(
        self,
        *,
        entity_type: str,
        name: str,
        description: str = '',
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        entity_id: str | None = None,
        confidence_score: float = 1.0,
        source_references: list[str] | None = None,
    ) -> KnowledgeEntity:
        self._ensure_permission("knowledge:create")
        entity_id = entity_id or str(uuid4())
        entity = KnowledgeEntity(
            entity_id=entity_id,
            name=name,
            description=description,
            entity_type=entity_type,
            metadata=metadata or {},
            tags=list(tags or []),
            created_at=self._timestamp(),
            updated_at=self._timestamp(),
            version=1,
            confidence_score=confidence_score,
            source_references=list(source_references or []),
        )
        with self._lock:
            self._entities[entity.entity_id] = entity
            self._graph_manager.add_node(entity.entity_id, entity.name, {"entity_type": entity.entity_type})
            self._search_manager.register_document(entity)
        self._persist_entity(entity)
        self._statistics_manager.record_update(1)
        self._statistics_manager.record_entity(1)
        self._emit_event("knowledge.entity.created", {"entity_id": entity.entity_id, "entity_type": entity.entity_type})
        self._audit("knowledge.entity.created", {"entity_id": entity.entity_id, "entity_type": entity.entity_type})
        return entity

    def get_entity(self, entity_id: str) -> KnowledgeEntity:
        with self._lock:
            entity = self._entities.get(entity_id)
        if entity is None:
            raise KnowledgeManagerError(f'Entity not found: {entity_id}')
        return entity

    def update_entity(self, entity_id: str, **changes: Any) -> KnowledgeEntity:
        self._ensure_permission("knowledge:update")
        with self._lock:
            entity = self._entities.get(entity_id)
            if entity is None:
                raise KnowledgeManagerError(f'Entity not found: {entity_id}')
            updated = KnowledgeEntity(
                entity_id=entity.entity_id,
                name=changes.get("name", entity.name),
                description=changes.get("description", entity.description),
                entity_type=changes.get("entity_type", entity.entity_type),
                metadata={**entity.metadata, **changes.get("metadata", {})},
                tags=list(changes.get("tags", entity.tags)),
                created_at=entity.created_at,
                updated_at=self._timestamp(),
                version=entity.version + 1,
                confidence_score=float(changes.get("confidence_score", entity.confidence_score)),
                source_references=list(changes.get("source_references", entity.source_references)),
            )
            self._entities[entity_id] = updated
            self._graph_manager.add_node(updated.entity_id, updated.name, {"entity_type": updated.entity_type})
            self._search_manager.register_document(updated)
        self._persist_entity(updated)
        self._statistics_manager.record_update(1)
        self._emit_event("knowledge.entity.updated", {"entity_id": entity_id})
        self._audit("knowledge.entity.updated", {"entity_id": entity_id})
        return updated

    def delete_entity(self, entity_id: str) -> None:
        self._ensure_permission("knowledge:delete")
        with self._lock:
            self._entities.pop(entity_id, None)
            self._relationships = {key: value for key, value in self._relationships.items() if value.source_entity_id != entity_id and value.target_entity_id != entity_id}
        self._memory_manager.delete_record(entity_id)
        self._statistics_manager.record_update(1)
        self._emit_event("knowledge.entity.deleted", {"entity_id": entity_id})
        self._audit("knowledge.entity.deleted", {"entity_id": entity_id})

    def list_entities(self) -> list[KnowledgeEntity]:
        with self._lock:
            return list(self._entities.values())

    def create_relationship(
        self,
        *,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeRelationship:
        self._ensure_permission("knowledge:update")
        relationship = KnowledgeRelationship(
            relationship_id=f"{source_entity_id}->{target_entity_id}:{relationship_type}",
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            metadata=metadata or {},
            confidence=confidence,
            timestamp=self._timestamp(),
        )
        with self._lock:
            self._relationships[relationship.relationship_id] = relationship
            self._graph_manager.add_node(source_entity_id, source_entity_id, {})
            self._graph_manager.add_node(target_entity_id, target_entity_id, {})
            self._graph_manager.add_edge(source_entity_id, target_entity_id, relationship_type, {**(metadata or {}), "confidence": confidence})
        self._persist_relationship(relationship)
        self._statistics_manager.record_update(1)
        self._emit_event("knowledge.relationship.created", {"relationship_id": relationship.relationship_id})
        self._audit("knowledge.relationship.created", {"relationship_id": relationship.relationship_id})
        return relationship

    def remove_relationship(self, relationship_id: str) -> None:
        self._ensure_permission("knowledge:update")
        with self._lock:
            relationship = self._relationships.pop(relationship_id, None)
        if relationship is not None:
            self._memory_manager.delete_record(relationship_id)
            self._emit_event("knowledge.relationship.removed", {"relationship_id": relationship_id})
            self._audit("knowledge.relationship.removed", {"relationship_id": relationship_id})

    def search_entities(self, query: str, **kwargs: Any) -> Any:
        self._ensure_permission("knowledge:search")
        self._statistics_manager.record_search(1)
        self._emit_event("knowledge.search.executed", {"query": query})
        self._audit("knowledge.search.executed", {"query": query})
        return self._search_manager.search(query, **kwargs)

    def lookup_by_id(self, entity_id: str) -> KnowledgeEntity | None:
        with self._lock:
            return self._entities.get(entity_id)

    def lookup_by_name(self, name: str) -> list[KnowledgeEntity]:
        normalized = name.lower()
        with self._lock:
            return [entity for entity in self._entities.values() if normalized in entity.name.lower()]

    def lookup_by_tag(self, tag: str) -> list[KnowledgeEntity]:
        normalized = tag.lower()
        with self._lock:
            return [entity for entity in self._entities.values() if any(normalized == item.lower() for item in entity.tags)]

    def lookup_by_type(self, entity_type: str) -> list[KnowledgeEntity]:
        with self._lock:
            return [entity for entity in self._entities.values() if entity.entity_type == entity_type]

    def lookup_by_metadata(self, key: str, value: Any) -> list[KnowledgeEntity]:
        with self._lock:
            return [entity for entity in self._entities.values() if entity.metadata.get(key) == value]

    def lookup_relationships(self, entity_id: str) -> list[KnowledgeRelationship]:
        return self._graph_manager.outgoing_relationships(entity_id) + self._graph_manager.incoming_relationships(entity_id)

    def begin_session(self, session_id: str) -> KnowledgeSession:
        session = KnowledgeSession(session_id=session_id, state='active')
        self._sessions[session_id] = session
        self._memory_manager.create_record(
            MemoryRecord(
                record_id=f"session:{session_id}",
                entries=[MemoryEntry(entry_id=f"session:{session_id}", type=MemoryType.SESSION, content={"kind": "session", "session_id": session_id}, metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()))],
                namespace="knowledge",
                metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()),
            )
        )
        return session

    def end_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            self._memory_manager.update_record(
                MemoryRecord(
                    record_id=f"session:{session_id}",
                    entries=[MemoryEntry(entry_id=f"session:{session_id}", type=MemoryType.SESSION, content={"kind": "session", "session_id": session_id, "state": "closed"}, metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()))],
                    namespace="knowledge",
                    metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()),
                )
            )

    def statistics(self) -> dict[str, int]:
        stats = self._statistics_manager.statistics()
        with self._lock:
            graph_stats = self._graph_manager.statistics()
            stats.update({
                "entity_count": max(len(self._entities), graph_stats["node_count"]),
                "relationship_count": max(len(self._relationships), graph_stats["edge_count"]),
                "graph_size": graph_stats["node_count"],
                "search_count": stats.get("search_count", 0),
                "update_count": stats.get("update_count", 0),
                "traversal_count": stats.get("traversal_count", 0),
                "cache_hits": stats.get("cache_hits", 0),
                "cache_misses": stats.get("cache_misses", 0),
            })
        return stats

    def health(self) -> dict[str, Any]:
        graph_stats = self._graph_manager.statistics()
        return {
            "graph_integrity": graph_stats["node_count"] >= 0,
            "index_integrity": True,
            "memory_connectivity": self._memory_manager is not None,
            "cache_health": True,
            "search_availability": True,
        }

    def register_kernel(self, kernel: Any) -> None:
        self._kernel = kernel

    def _hydrate_from_memory(self) -> None:
        with self._lock:
            for record in self._memory_manager.list_records():
                for entry in record.entries:
                    if entry.type != MemoryType.KNOWLEDGE:
                        continue
                    payload = entry.content or {}
                    kind = payload.get("kind")
                    if kind == "entity":
                        entity = KnowledgeEntity(**payload.get("entity", {}))
                        self._entities[entity.entity_id] = entity
                        self._graph_manager.add_node(entity.entity_id, entity.name, {"entity_type": entity.entity_type})
                        self._search_manager.register_document(entity)
                    elif kind == "relationship":
                        relationship = KnowledgeRelationship(**payload.get("relationship", {}))
                        self._relationships[relationship.relationship_id] = relationship
                        self._graph_manager.add_edge(relationship.source_entity_id, relationship.target_entity_id, relationship.relationship_type, relationship.metadata)
                    elif kind == "source":
                        source = payload.get("source")
                        if source is not None:
                            self._source_manager.register_source(KnowledgeSource(**source))

    def _persist_entity(self, entity: KnowledgeEntity) -> None:
        self._memory_manager.create_record(
            MemoryRecord(
                record_id=entity.entity_id,
                entries=[MemoryEntry(entry_id=entity.entity_id, type=MemoryType.KNOWLEDGE, content={"kind": "entity", "entity": {k: (v if not isinstance(v, list) else list(v) ) for k, v in entity.__dict__.items()}}, metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp(), tags=entity.tags, attributes={"entity_type": entity.entity_type}))],
                namespace="knowledge",
                metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp(), tags=entity.tags, attributes={"entity_type": entity.entity_type}),
            )
        )

    def _persist_relationship(self, relationship: KnowledgeRelationship) -> None:
        self._memory_manager.create_record(
            MemoryRecord(
                record_id=relationship.relationship_id,
                entries=[MemoryEntry(entry_id=relationship.relationship_id, type=MemoryType.KNOWLEDGE, content={"kind": "relationship", "relationship": {k: (v if not isinstance(v, list) else list(v) ) for k, v in relationship.__dict__.items()}}, metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp(), attributes={"relationship_type": relationship.relationship_type}))],
                namespace="knowledge",
                metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp(), attributes={"relationship_type": relationship.relationship_type}),
            )
        )

    def _persist_source(self, source: KnowledgeSource) -> None:
        self._memory_manager.create_record(
            MemoryRecord(
                record_id=source.source_id,
                entries=[MemoryEntry(entry_id=source.source_id, type=MemoryType.KNOWLEDGE, content={"kind": "source", "source": {"source_id": source.source_id, "source_type": source.source_type.value, "uri": source.uri, "metadata": {"title": source.metadata.title, "tags": list(source.metadata.tags), "attributes": dict(source.metadata.attributes)}}}, metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()))],
                namespace="knowledge",
                metadata=MemoryMetadata(namespace="knowledge", created_by="knowledge-engine", created_at=self._timestamp(), updated_at=self._timestamp()),
            )
        )

    def _ensure_permission(self, permission_id: str) -> None:
        if self._security_manager is None:
            return
        permission_manager = getattr(self._security_manager, "get_permission_manager", lambda: None)()
        if permission_manager is None or not hasattr(permission_manager, "has_permission"):
            return
        if not permission_manager.has_permission("knowledge-engine", permission_id):
            raise KnowledgeManagerError(f"Permission denied for {permission_id}")

    def _audit(self, event: str, metadata: dict[str, Any]) -> None:
        if self._security_manager is None:
            return
        audit_manager = getattr(self._security_manager, "get_audit_manager", lambda: None)()
        if audit_manager is not None and hasattr(audit_manager, "record_event"):
            audit_manager.record_event(event, "knowledge-engine", metadata)

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event_name, payload, metadata={"source": "knowledge-engine"})
        if self._observability_manager is not None:
            recorder = getattr(self._observability_manager, "event_recorder", None)
            if recorder is not None and hasattr(recorder, "record"):
                recorder.record({"event": event_name, **payload})

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


from tangku_agentos.knowledge_engine.models import KnowledgeSourceType

