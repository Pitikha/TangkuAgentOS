from __future__ import annotations

from pathlib import Path

from tangku_agentos.context_engine import ContextConfiguration, ContextManager, ContextMetadata, ContextObject, ContextPriority, ContextSegment, ContextSource
from tangku_agentos.core_runtime.event_bus import EventBus


class DummySecurityManager:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    def get_permission_manager(self) -> object:
        class PermissionManager:
            def has_permission(self, role_id: str, permission_id: str) -> bool:
                return True

        return PermissionManager()

    def get_audit_manager(self) -> object:
        class AuditManager:
            def __init__(self) -> None:
                self.events: list[tuple[str, str, dict]] = []

            def record_event(self, event: str, identity: str, metadata: dict | None = None) -> None:
                self.events.append((event, identity, metadata or {}))

        return AuditManager()


class DummyObservabilityManager:
    def __init__(self) -> None:
        self.events: list[dict] = []

    @property
    def event_recorder(self) -> object:
        class Recorder:
            def __init__(self, owner: DummyObservabilityManager) -> None:
                self.owner = owner

            def record(self, event: object) -> None:
                self.owner.events.append({"event": event})

        return Recorder(self)


def test_context_engine_assembly_merge_persistence_and_security(tmp_path: Path) -> None:
    event_bus = EventBus()
    events: list[tuple[str, dict]] = []
    event_bus.subscribe("context.created", lambda name, payload: events.append((name, payload)))

    manager = ContextManager(
        db_path=str(tmp_path / "context.sqlite"),
        event_bus=event_bus,
        security_manager=DummySecurityManager(),
        observability_manager=DummyObservabilityManager(),
    )

    workspace_context = ContextObject(
        context_id="workspace-context",
        segments=[ContextSegment(segment_id="ws-1", content="workspace: alpha", source=ContextSource.WORKSPACE, priority=ContextPriority.HIGH)],
    )
    memory_context = ContextObject(
        context_id="memory-context",
        segments=[ContextSegment(segment_id="mem-1", content="memory: previous turn", source=ContextSource.MEMORY, priority=ContextPriority.MEDIUM)],
    )

    manager.create_context(workspace_context)
    manager.create_context(memory_context)
    merged = manager.merge_context([workspace_context, memory_context], metadata=ContextMetadata(source=ContextSource.CONVERSATION, attributes={"user": "alice"}))

    assert merged.context_id.startswith("merged")
    assert len(merged.segments) >= 2
    assert merged.statistics.segment_count >= 2

    trimmed = manager.trim_context(merged, max_tokens=3)
    assert len(trimmed.segments) <= 2

    snapshot = manager.snapshot_context(merged.context_id)
    assert snapshot.context_id == merged.context_id

    restored = manager.restore_context(merged.context_id)
    assert restored.context_id == merged.context_id

    search_results = manager.search_context("workspace")
    assert search_results[0].context_id == workspace_context.context_id

    contexts = manager.list_contexts()
    assert any(context.context_id == merged.context_id for context in contexts)

    assert events


def test_context_engine_build_and_filter_sensitive_content() -> None:
    manager = ContextManager(security_manager=DummySecurityManager())
    metadata = ContextMetadata(
        source=ContextSource.CONVERSATION,
        attributes={
            "content": "User token secret-value and repo path /tmp",
            "workspace": "demo",
            "repository": "repo-a",
            "active_goal": "Ship feature",
            "preferences": {"mode": "fast"},
        },
    )
    context = manager.build_context(metadata)
    assert context.context_id
    assert "secret-value" not in " ".join(segment.content for segment in context.segments)
    assert "token" not in " ".join(segment.content for segment in context.segments)
