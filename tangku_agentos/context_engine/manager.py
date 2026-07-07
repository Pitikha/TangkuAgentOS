from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Iterable

from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .builder import ContextBuilder
from .cache import ContextCache
from .compressor import ContextCompressor
from .exceptions import ContextManagerError
from .interfaces import ContextManagerInterface
from .models import ContextBudget, ContextConfiguration, ContextMetadata, ContextObject, ContextPriority, ContextReference, ContextSegment, ContextSource, ContextStatistics
from .optimizer import ContextOptimizer
from .provider import ContextProvider
from .registry import ContextRegistry
from .resolver import ContextResolver
from .snapshot import ContextSnapshotManager
from .assembler import ContextAssembler
from .budget import ContextBudgetManager
from .session import ContextSessionManager


class ContextManager(ContextManagerInterface):
    """Central context manager that coordinates building, assembly, resolution, and snapshots."""

    def __init__(
        self,
        registry: ContextRegistry | None = None,
        builder: ContextBuilder | None = None,
        assembler: ContextAssembler | None = None,
        cache: ContextCache | None = None,
        resolver: ContextResolver | None = None,
        snapshot_manager: ContextSnapshotManager | None = None,
        optimizer: ContextOptimizer | None = None,
        compressor: ContextCompressor | None = None,
        budget_manager: ContextBudgetManager | None = None,
        session_manager: ContextSessionManager | None = None,
        db_path: str | None = None,
        event_bus: Any | None = None,
        security_manager: Any | None = None,
        observability_manager: Any | None = None,
    ) -> None:
        self._registry = registry or ContextRegistry()
        self._builder = builder or ContextBuilder()
        self._assembler = assembler or ContextAssembler()
        self._cache = cache or ContextCache()
        self._resolver = resolver or ContextResolver(self._registry, self._cache)
        self._snapshot_manager = snapshot_manager or ContextSnapshotManager()
        self._optimizer = optimizer or ContextOptimizer()
        self._compressor = compressor or ContextCompressor()
        self._budget_manager = budget_manager or ContextBudgetManager(self._compressor, self._optimizer)
        self._session_manager = session_manager or ContextSessionManager()
        self._provider = ContextProvider(self._registry, self._cache)
        self._memory_manager = MemoryManager(db_path=db_path)
        self._event_bus = event_bus
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._contexts: dict[str, ContextObject] = {}
        self._snapshots: dict[str, ContextObject] = {}
        self._lock = RLock()
        self._hydrate_from_memory()

    def create_context(self, context: ContextObject) -> None:
        self._prepare_context(context)
        self._register_context(context)
        self._persist_context(context)
        self._emit_event("context.created", {"context_id": context.context_id})
        self._audit("context.created", {"context_id": context.context_id})

    def get_context(self, context_id: str) -> ContextObject:
        cached = self._cache.retrieve(context_id)
        if cached is not None:
            return cached
        try:
            return self._registry.get(context_id)
        except Exception as error:
            raise ContextManagerError(str(error)) from error

    def update_context(self, context: ContextObject) -> None:
        self._prepare_context(context)
        self._register_context(context)
        self._persist_context(context)
        self._emit_event("context.updated", {"context_id": context.context_id})
        self._audit("context.updated", {"context_id": context.context_id})

    def delete_context(self, context_id: str) -> None:
        self._ensure_permission("context:delete")
        self._registry.unregister(context_id)
        self._contexts.pop(context_id, None)
        self._snapshots.pop(context_id, None)
        self._memory_manager.delete_record(context_id)
        self._emit_event("context.discarded", {"context_id": context_id})
        self._audit("context.discarded", {"context_id": context_id})

    def build_context(self, metadata: ContextMetadata) -> ContextObject:
        self._ensure_permission("context:create")
        context = self._builder.build(metadata)
        self._sanitize_context(context)
        self._prepare_context(context)
        self._register_context(context)
        self._persist_context(context)
        self._emit_event("context.created", {"context_id": context.context_id})
        return context

    def merge_context(self, contexts: Iterable[ContextObject], metadata: ContextMetadata | None = None) -> ContextObject:
        self._ensure_permission("context:update")
        merged = self._assembler.assemble(list(contexts), metadata=metadata)
        self._sanitize_context(merged)
        self._prepare_context(merged)
        self._register_context(merged)
        self._persist_context(merged)
        self._emit_event("context.merged", {"context_id": merged.context_id})
        self._audit("context.merged", {"context_id": merged.context_id})
        return merged

    def snapshot_context(self, context_id: str) -> ContextObject:
        context = self.get_context(context_id)
        self._snapshots[context_id] = context
        self._snapshot_manager.snapshot(context)
        self._emit_event("context.snapshot_created", {"context_id": context_id})
        self._audit("context.snapshot_created", {"context_id": context_id})
        return context

    def restore_context(self, context_id: str) -> ContextObject:
        snapshot = self._snapshots.get(context_id) or self._snapshot_manager.get_snapshot(context_id)
        self._register_context(snapshot)
        self._emit_event("context.restored", {"context_id": context_id})
        self._audit("context.restored", {"context_id": context_id})
        return snapshot

    def search_context(self, query: str) -> list[ContextObject]:
        self._ensure_permission("context:search")
        normalized = query.lower()
        results = [context for context in self._registry.list() if normalized in " ".join(segment.content.lower() for segment in context.segments)]
        self._emit_event("context.search", {"query": query, "count": len(results)})
        return results

    def list_contexts(self) -> list[ContextObject]:
        return self._registry.list()

    def trim_context(self, context: ContextObject, max_tokens: int | None = None) -> ContextObject:
        if max_tokens is None:
            max_tokens = context.configuration.max_tokens
        trimmed = ContextObject(
            context_id=context.context_id,
            segments=[],
            references=list(context.references),
            priority=context.priority,
            statistics=ContextStatistics(),
            configuration=ContextConfiguration(max_tokens=max_tokens),
            metadata=dict(context.metadata),
        )
        token_total = 0
        for segment in sorted(context.segments, key=lambda item: (item.priority.value != "critical", item.segment_id)):
            segment_tokens = len(segment.content.split())
            if token_total + segment_tokens > max_tokens:
                continue
            trimmed.segments.append(segment)
            token_total += segment_tokens
        self._prepare_context(trimmed)
        self._register_context(trimmed)
        return trimmed

    def assemble_context(self, contexts: Iterable[ContextObject], metadata: ContextMetadata | None = None) -> ContextObject:
        assembled = self._assembler.assemble(list(contexts), metadata=metadata)
        self._sanitize_context(assembled)
        self._prepare_context(assembled)
        self._register_context(assembled)
        self._persist_context(assembled)
        return assembled

    def resolve_context(self, reference_id: str) -> ContextObject:
        return self._resolver.resolve(reference_id)

    def optimize_context(self, context: ContextObject) -> ContextObject:
        optimized = self._optimizer.optimize(context)
        self._prepare_context(optimized)
        self._register_context(optimized)
        return optimized

    def compress_context(self, context: ContextObject) -> ContextObject:
        compressed = self._compressor.compress(context)
        self._prepare_context(compressed)
        self._register_context(compressed)
        return compressed

    def allocate_budget(self, context: ContextObject, budget: ContextBudget | None = None) -> ContextObject:
        return self._budget_manager.allocate(context, budget)

    def create_session(self, session_id: str, context_id: str | None = None) -> None:
        self._session_manager.create_session(session_id)
        if context_id is not None:
            self._session_manager.attach_context(session_id, context_id)

    def attach_context_to_session(self, session_id: str, context_id: str) -> None:
        self._session_manager.attach_context(session_id, context_id)

    def get_session_contexts(self, session_id: str) -> list[str]:
        return self._session_manager.list_contexts(session_id)

    def _prepare_context(self, context: ContextObject) -> None:
        if not context.segments:
            context.segments = [
                ContextSegment(
                    segment_id=f"{context.context_id}-default",
                    content="",
                    source=ContextSource.CONFIGURATION,
                    priority=ContextPriority.MEDIUM,
                )
            ]
        self._ensure_statistics(context)
        context.configuration = ContextConfiguration(
            max_tokens=context.configuration.max_tokens or 4096,
            compression_enabled=context.configuration.compression_enabled,
            optimizer_enabled=context.configuration.optimizer_enabled,
            retention_days=context.configuration.retention_days,
            metadata=context.configuration.metadata,
        )

    def _ensure_statistics(self, context: ContextObject) -> None:
        counts = Counter(segment.source for segment in context.segments)
        context.statistics.segment_count = len(context.segments)
        context.statistics.token_count = sum(len(segment.content.split()) for segment in context.segments)
        context.statistics.source_counts = {source: counts.get(source, 0) for source in ContextSource}
        context.statistics.metadata = {"context_id": context.context_id, "priority": context.priority.value}

    def _register_context(self, context: ContextObject) -> None:
        with self._lock:
            self._contexts[context.context_id] = context
            self._registry.register(context)
            self._cache.store(context)

    def _persist_context(self, context: ContextObject) -> None:
        payload = {
            "kind": "context",
            "context": {
                "context_id": context.context_id,
                "segments": [
                    {
                        "segment_id": segment.segment_id,
                        "content": segment.content,
                        "source": segment.source.value,
                        "priority": segment.priority.value,
                        "metadata": dict(segment.metadata),
                    }
                    for segment in context.segments
                ],
                "references": [
                    {
                        "reference_id": ref.reference_id,
                        "source": ref.source.value,
                        "metadata": dict(ref.metadata),
                    }
                    for ref in context.references
                ],
                "priority": context.priority.value,
                "metadata": dict(context.metadata),
            },
        }
        self._memory_manager.create_record(
            MemoryRecord(
                record_id=context.context_id,
                entries=[
                    MemoryEntry(
                        entry_id=context.context_id,
                        type=MemoryType.KNOWLEDGE,
                        content=payload,
                        metadata=MemoryMetadata(namespace="context", created_by="context-engine", created_at=self._timestamp(), updated_at=self._timestamp()),
                    )
                ],
                namespace="context",
                metadata=MemoryMetadata(namespace="context", created_by="context-engine", created_at=self._timestamp(), updated_at=self._timestamp()),
            )
        )

    def _hydrate_from_memory(self) -> None:
        for record in self._memory_manager.list_records():
            for entry in record.entries:
                if entry.type != MemoryType.KNOWLEDGE:
                    continue
                payload = entry.content or {}
                if payload.get("kind") != "context":
                    continue
                context_payload = payload.get("context", {})
                segments = [ContextSegment(segment_id=item["segment_id"], content=item["content"], source=ContextSource(item["source"]), priority=ContextPriority(item.get("priority", "medium")), metadata=item.get("metadata", {})) for item in context_payload.get("segments", [])]
                references = [ContextReference(reference_id=item["reference_id"], source=ContextSource(item["source"]), metadata=item.get("metadata", {})) for item in context_payload.get("references", [])]
                context = ContextObject(
                    context_id=context_payload["context_id"],
                    segments=segments,
                    references=references,
                    priority=ContextPriority(context_payload.get("priority", "medium")),
                    statistics=ContextStatistics(),
                    configuration=ContextConfiguration(),
                    metadata=context_payload.get("metadata", {}),
                )
                self._register_context(context)

    def _sanitize_context(self, context: ContextObject) -> None:
        sensitive_terms = ["secret", "token", "password", "apikey", "api_key", "authorization"]
        sanitized_segments: list[ContextSegment] = []
        for segment in context.segments:
            text = segment.content
            lowered = text.lower()
            if any(term in lowered for term in sensitive_terms):
                sanitized_text = text
                for term in sensitive_terms:
                    sanitized_text = sanitized_text.replace(term, "[redacted]")
                text = sanitized_text
            sanitized_segments.append(ContextSegment(segment_id=segment.segment_id, content=text, source=segment.source, priority=segment.priority, metadata=dict(segment.metadata)))
        context.segments = sanitized_segments

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event_name, payload, metadata={"source": "context-engine"})
        if self._observability_manager is not None:
            recorder = getattr(self._observability_manager, "event_recorder", None)
            if recorder is not None and hasattr(recorder, "record"):
                recorder.record({"event": event_name, **payload})

    def _audit(self, event: str, metadata: dict[str, Any]) -> None:
        if self._security_manager is None:
            return
        audit_manager = getattr(self._security_manager, "get_audit_manager", lambda: None)()
        if audit_manager is not None and hasattr(audit_manager, "record_event"):
            audit_manager.record_event(event, "context-engine", metadata)

    def _ensure_permission(self, permission_id: str) -> None:
        if self._security_manager is None:
            return
        permission_manager = getattr(self._security_manager, "get_permission_manager", lambda: None)()
        if permission_manager is None or not hasattr(permission_manager, "has_permission"):
            return
        if not permission_manager.has_permission("context-engine", permission_id):
            raise ContextManagerError(f"Permission denied for {permission_id}")

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
