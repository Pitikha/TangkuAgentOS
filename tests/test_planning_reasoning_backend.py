from __future__ import annotations

from pathlib import Path

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.memory_engine import MemoryManager
from tangku_agentos.planning_runtime import PlanningManager
from tangku_agentos.planning_runtime.models import PlanCheckpoint, PlanDependency, PlanStage, PlanState
from tangku_agentos.reasoning_runtime import ReasoningManager
from tangku_agentos.reasoning_runtime.models import ReasoningMode


class DummySecurityManager:
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
        self.records: list[dict] = []

    @property
    def event_recorder(self) -> object:
        class Recorder:
            def __init__(self, owner: DummyObservabilityManager) -> None:
                self.owner = owner

            def record(self, event: object) -> None:
                self.owner.records.append({"event": event})

        return Recorder(self)


def test_planning_runtime_goal_decomposition_and_execution(tmp_path: Path) -> None:
    event_bus = EventBus()
    events: list[tuple[str, dict]] = []
    event_bus.subscribe("plan.created", lambda name, payload: events.append((name, payload)))
    event_bus.subscribe("plan.completed", lambda name, payload: events.append((name, payload)))

    manager = PlanningManager(
        db_path=str(tmp_path / "planning.sqlite"),
        event_bus=event_bus,
        security_manager=DummySecurityManager(),
        observability_manager=DummyObservabilityManager(),
    )

    plan_id = manager.create_plan(goal="Build a web application")
    assert plan_id

    plan = manager.get_plan(plan_id)
    assert plan.goal == "Build a web application"
    assert plan.state == PlanState.DRAFT

    stage1 = PlanStage(stage_id="setup", name="Environment Setup")
    manager.add_stage(plan_id, stage1)

    stage2 = PlanStage(stage_id="dev", name="Development")
    manager.add_stage(plan_id, stage2)

    dep = PlanDependency(dependency_id="dep-1", target="dev", depends_on="setup")
    manager.add_dependency(plan_id, dep)

    checkpoint = PlanCheckpoint(checkpoint_id="check-1", plan_id=plan_id, stage_id="setup")
    manager.add_checkpoint(plan_id, checkpoint)

    manager.start_plan(plan_id)
    updated_plan = manager.get_plan(plan_id)
    assert updated_plan.state == PlanState.ACTIVE

    manager.pause_plan(plan_id)
    paused_plan = manager.get_plan(plan_id)
    assert paused_plan.state == PlanState.PAUSED

    manager.resume_plan(plan_id)
    resumed_plan = manager.get_plan(plan_id)
    assert resumed_plan.state == PlanState.ACTIVE

    manager.complete_plan(plan_id)
    completed_plan = manager.get_plan(plan_id)
    assert completed_plan.state == PlanState.COMPLETED

    plan_list = manager.list_plans()
    assert any(p.plan_id == plan_id for p in plan_list)

    assert events


def test_planning_runtime_replanning_and_task_modification(tmp_path: Path) -> None:
    manager = PlanningManager(db_path=str(tmp_path / "planning.sqlite"))

    plan_id = manager.create_plan(goal="Deploy service")
    stage1 = PlanStage(stage_id="build", name="Build")
    manager.add_stage(plan_id, stage1)

    stage2 = PlanStage(stage_id="test", name="Test")
    manager.add_stage(plan_id, stage2)

    plan = manager.get_plan(plan_id)
    assert len(plan.stages) == 2

    stage3 = PlanStage(stage_id="deploy", name="Deploy")
    manager.insert_stage(plan_id, stage3, after_stage="test")
    updated_plan = manager.get_plan(plan_id)
    assert len(updated_plan.stages) == 3

    manager.remove_stage(plan_id, "test")
    final_plan = manager.get_plan(plan_id)
    assert len(final_plan.stages) == 2

    manager.start_plan(plan_id)
    manager.cancel_plan(plan_id)
    cancelled_plan = manager.get_plan(plan_id)
    assert cancelled_plan.state == PlanState.CANCELLED


def test_reasoning_runtime_decision_making_and_trace_persistence(tmp_path: Path) -> None:
    event_bus = EventBus()
    events: list[tuple[str, dict]] = []
    event_bus.subscribe("reasoning.decision_created", lambda name, payload: events.append((name, payload)))

    manager = ReasoningManager(
        db_path=str(tmp_path / "reasoning.sqlite"),
        event_bus=event_bus,
        security_manager=DummySecurityManager(),
        observability_manager=DummyObservabilityManager(),
    )

    context = manager.create_context(
        context_id="reasoning-1",
        subject_id="task-1",
        mode=ReasoningMode.REFLECTIVE,
        metadata={"goal": "analyze request"},
    )
    assert context.context_id == "reasoning-1"
    assert context.mode == ReasoningMode.REFLECTIVE

    session = manager.create_session(context.context_id, metadata={"user": "alice"})
    assert session.session_id
    assert session.context_id == context.context_id

    decision = manager.reason(
        session.session_id,
        query="Which tool should I use?",
        available_tools=["tool_a", "tool_b"],
        context_data={"task": "analyze", "priority": "high"},
    )
    assert decision
    assert decision.get("selected_tool") in ["tool_a", "tool_b"]

    trace = manager.get_reasoning_trace(session.session_id)
    assert trace.trace_id == session.session_id

    manager.archive_session(session.session_id)
    archived = manager.get_session(session.session_id)
    assert archived.metadata.get("archived") is True

    assert events


def test_reasoning_runtime_provider_routing_and_model_selection() -> None:
    manager = ReasoningManager()

    context = manager.create_context(context_id="analyze", subject_id="model-selection")
    session = manager.create_session(context.context_id)

    decision = manager.decide_provider(
        session.session_id,
        task="generate_code",
        available_providers=["openai", "anthropic", "local"],
        context_data={"language": "python", "length": "short"},
    )
    assert decision.get("provider") in ["openai", "anthropic", "local"]

    model_decision = manager.select_model(
        session.session_id,
        provider=decision.get("provider"),
        task_type="code_generation",
        available_models=["gpt-4", "gpt-3.5", "claude-3"],
    )
    assert model_decision.get("model")

    evaluation = manager.evaluate(
        session.session_id,
        decision={"provider": "openai", "model": "gpt-4"},
        outcome={"success": True, "latency": 1.5},
    )
    assert evaluation.get("score") is not None


def test_planning_runtime_update_and_rebuild_api() -> None:
    manager = PlanningManager()
    plan_id = manager.create_plan(goal="Launch feature")

    updated_plan = manager.update_plan(plan_id, state=PlanState.ACTIVE, metadata={"priority": "high"})
    assert updated_plan is not None
    assert updated_plan.state == PlanState.ACTIVE
    assert updated_plan.metadata["priority"] == "high"

    rebuilt_plan = manager.rebuild_plan(plan_id, goal="Launch feature with validation", metadata={"replanned": True})
    assert rebuilt_plan is not None
    assert rebuilt_plan.goal == "Launch feature with validation"
    assert rebuilt_plan.metadata["replanned"] is True


def test_reasoning_runtime_session_restore_and_listing() -> None:
    manager = ReasoningManager()
    context = manager.create_context(context_id="restore-check", subject_id="session")
    session = manager.create_reasoning_session(context.context_id, metadata={"user": "alice"})

    sessions = manager.list_sessions()
    assert any(item.session_id == session.session_id for item in sessions)

    manager.archive_session(session.session_id)
    restored_session = manager.restore_session(session.session_id)
    assert restored_session is not None
    assert restored_session.session_id == session.session_id
    assert restored_session.metadata.get("archived") is None


def test_planning_and_reasoning_integration() -> None:
    planning_mgr = PlanningManager()
    reasoning_mgr = ReasoningManager()

    plan_id = planning_mgr.create_plan(goal="Ship feature")
    stage = PlanStage(stage_id="phase1", name="Phase 1")
    planning_mgr.add_stage(plan_id, stage)

    planning_mgr.start_plan(plan_id)
    plan = planning_mgr.get_plan(plan_id)

    context = reasoning_mgr.create_context(context_id=plan_id, subject_id=plan_id)
    session = reasoning_mgr.create_session(context.context_id, metadata={"plan_id": plan_id})

    decision = reasoning_mgr.reason(session.session_id, query="How to proceed?", context_data={"plan": plan_id})
    assert decision

    planning_mgr.complete_plan(plan_id)
    final_plan = planning_mgr.get_plan(plan_id)
    assert final_plan.state == PlanState.COMPLETED
