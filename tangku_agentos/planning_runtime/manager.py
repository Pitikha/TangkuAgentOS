from __future__ import annotations

from threading import RLock
from typing import Any
from uuid import uuid4

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .models import Plan, PlanCheckpoint, PlanDependency, PlanStage, PlanState


class PlanningManager:
    """Coordinate plan lifecycle, registration, and persistence."""

    def __init__(
        self,
        db_path: str | None = None,
        event_bus: EventBus | None = None,
        security_manager: Any | None = None,
        observability_manager: Any | None = None,
    ) -> None:
        self._plans: dict[str, Plan] = {}
        self._lock = RLock()
        self._memory: MemoryManager = MemoryManager(db_path) if db_path else MemoryManager()
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._hydrate_from_memory()

    def create_plan(self, goal: str, *, metadata: dict[str, object] | None = None) -> str:
        self._ensure_permission("plan.create")
        plan_id = str(uuid4())
        normalized_metadata = self._normalize_metadata(metadata)
        plan = self._build_plan(plan_id, goal, normalized_metadata, auto_decompose=False)
        with self._lock:
            self._plans[plan_id] = plan
        self._persist_plan(plan)
        self._emit_plan_event("plan_created", {"plan_id": plan_id, "goal": goal, "metadata": normalized_metadata})
        self._audit("plan.created", plan_id, {"goal": goal, "metadata": normalized_metadata})
        return plan_id

    def update_plan(
        self,
        plan_id: str,
        *,
        goal: str | None = None,
        state: PlanState | str | None = None,
        stages: list[PlanStage] | tuple[PlanStage, ...] | None = None,
        dependencies: list[PlanDependency] | tuple[PlanDependency, ...] | None = None,
        checkpoints: list[PlanCheckpoint] | tuple[PlanCheckpoint, ...] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Plan | None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=goal if goal is not None else plan.goal,
                state=self._coerce_state(state, plan.state),
                stages=tuple(stages) if stages is not None else plan.stages,
                dependencies=tuple(dependencies) if dependencies is not None else plan.dependencies,
                checkpoints=tuple(checkpoints) if checkpoints is not None else plan.checkpoints,
                metadata={**plan.metadata, **(metadata or {})},
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("plan_updated", {"plan_id": plan_id, "goal": updated_plan.goal, "state": updated_plan.state.value})
        self._audit("plan.updated", plan_id, {"state": updated_plan.state.value})
        return updated_plan

    def get_plan(self, plan_id: str) -> Plan | None:
        with self._lock:
            return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        with self._lock:
            return list(self._plans.values())

    def execute_plan(self, plan_id: str) -> Plan | None:
        return self.start_plan(plan_id)

    def add_stage(self, plan_id: str, stage: PlanStage) -> None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return
            stages = list(plan.stages) + [stage]
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=plan.state,
                stages=tuple(stages),
                dependencies=plan.dependencies,
                checkpoints=plan.checkpoints,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("task_added", {"plan_id": plan_id, "stage_id": stage.stage_id, "name": stage.name})
        self._audit("plan.stage_added", plan_id, {"stage_id": stage.stage_id})

    def insert_stage(self, plan_id: str, stage: PlanStage, after_stage: str) -> None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return
            stages = list(plan.stages)
            insert_index = None
            for i, s in enumerate(stages):
                if s.stage_id == after_stage:
                    insert_index = i + 1
                    break
            if insert_index is not None:
                stages.insert(insert_index, stage)
            else:
                stages.append(stage)
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=plan.state,
                stages=tuple(stages),
                dependencies=plan.dependencies,
                checkpoints=plan.checkpoints,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("task_added", {"plan_id": plan_id, "stage_id": stage.stage_id, "name": stage.name})
        self._audit("plan.stage_inserted", plan_id, {"stage_id": stage.stage_id})

    def remove_stage(self, plan_id: str, stage_id: str) -> None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return
            stages = [s for s in plan.stages if s.stage_id != stage_id]
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=plan.state,
                stages=tuple(stages),
                dependencies=plan.dependencies,
                checkpoints=plan.checkpoints,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("plan_updated", {"plan_id": plan_id, "removed_stage": stage_id})
        self._audit("plan.stage_removed", plan_id, {"stage_id": stage_id})

    def add_dependency(self, plan_id: str, dependency: PlanDependency) -> None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return
            dependencies = list(plan.dependencies) + [dependency]
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=plan.state,
                stages=plan.stages,
                dependencies=tuple(dependencies),
                checkpoints=plan.checkpoints,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("plan_updated", {"plan_id": plan_id, "dependency_id": dependency.dependency_id})
        self._audit("plan.dependency_added", plan_id, {"dependency_id": dependency.dependency_id})

    def add_checkpoint(self, plan_id: str, checkpoint: PlanCheckpoint) -> None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return
            checkpoints = list(plan.checkpoints) + [checkpoint]
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=plan.state,
                stages=plan.stages,
                dependencies=plan.dependencies,
                checkpoints=tuple(checkpoints),
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event("plan_updated", {"plan_id": plan_id, "checkpoint_id": checkpoint.checkpoint_id})
        self._audit("plan.checkpoint_added", plan_id, {"checkpoint_id": checkpoint.checkpoint_id})

    def start_plan(self, plan_id: str) -> Plan | None:
        return self._transition_state(plan_id, PlanState.ACTIVE, event_name="plan_started")

    def pause_plan(self, plan_id: str) -> Plan | None:
        return self._transition_state(plan_id, PlanState.PAUSED, event_name="plan_paused")

    def resume_plan(self, plan_id: str) -> Plan | None:
        return self._transition_state(plan_id, PlanState.ACTIVE, event_name="plan_resumed")

    def cancel_plan(self, plan_id: str) -> Plan | None:
        return self._transition_state(plan_id, PlanState.CANCELLED, event_name="plan_cancelled")

    def complete_plan(self, plan_id: str) -> Plan | None:
        return self._transition_state(plan_id, PlanState.COMPLETED, event_name="plan_completed")

    def rebuild_plan(self, plan_id: str, *, goal: str | None = None, metadata: dict[str, object] | None = None) -> Plan | None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            rebuilt_plan = self._build_plan(
                plan_id,
                goal or plan.goal,
                {**plan.metadata, **(metadata or {})},
                base_plan=plan,
                auto_decompose=True,
            )
            self._plans[plan_id] = rebuilt_plan
        self._persist_plan(rebuilt_plan)
        self._emit_plan_event("plan_updated", {"plan_id": plan_id, "rebuilt": True})
        self._audit("plan.rebuilt", plan_id, {"goal": rebuilt_plan.goal})
        return rebuilt_plan

    def pause(self, plan_id: str) -> Plan | None:
        return self.pause_plan(plan_id)

    def resume(self, plan_id: str) -> Plan | None:
        return self.resume_plan(plan_id)

    def cancel(self, plan_id: str) -> Plan | None:
        return self.cancel_plan(plan_id)

    def complete(self, plan_id: str) -> Plan | None:
        return self.complete_plan(plan_id)

    def _transition_state(self, plan_id: str, state: PlanState, *, event_name: str) -> Plan | None:
        self._ensure_permission("plan.update")
        with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None:
                return None
            updated_plan = Plan(
                plan_id=plan.plan_id,
                goal=plan.goal,
                state=state,
                stages=plan.stages,
                dependencies=plan.dependencies,
                checkpoints=plan.checkpoints,
                metadata=plan.metadata,
            )
            self._plans[plan_id] = updated_plan
        self._persist_plan(updated_plan)
        self._emit_plan_event(event_name, {"plan_id": plan_id, "state": state.value})
        self._audit(f"plan.{event_name}", plan_id, {"state": state.value})
        return updated_plan

    def _build_plan(
        self,
        plan_id: str,
        goal: str,
        metadata: dict[str, object],
        *,
        base_plan: Plan | None = None,
        auto_decompose: bool = True,
    ) -> Plan:
        if auto_decompose:
            stages, dependencies, checkpoints = self._decompose_goal(goal, plan_id, metadata)
        else:
            stages, dependencies, checkpoints = [], [], []
        state = base_plan.state if base_plan is not None else PlanState.DRAFT
        return Plan(
            plan_id=plan_id,
            goal=goal,
            state=state,
            stages=tuple(stages),
            dependencies=tuple(dependencies),
            checkpoints=tuple(checkpoints),
            metadata=metadata,
        )

    def _decompose_goal(self, goal: str, plan_id: str, metadata: dict[str, object]) -> tuple[list[PlanStage], list[PlanDependency], list[PlanCheckpoint]]:
        stage_names = self._infer_stage_names(goal)
        stages: list[PlanStage] = []
        for index, name in enumerate(stage_names):
            stage_id = f"stage-{index + 1}"
            stages.append(PlanStage(stage_id=stage_id, name=name, status="pending", metadata={"priority": index + 1, "goal": goal}))

        dependencies: list[PlanDependency] = []
        for index in range(1, len(stages)):
            dependencies.append(PlanDependency(dependency_id=f"dep-{index}", target=stages[index].stage_id, depends_on=stages[index - 1].stage_id))

        checkpoints: list[PlanCheckpoint] = []
        for stage in stages:
            checkpoints.append(PlanCheckpoint(checkpoint_id=f"checkpoint-{stage.stage_id}", plan_id=plan_id, stage_id=stage.stage_id, metadata={"milestone": stage.name}))

        if metadata.get("constraints"):
            constraints = metadata.get("constraints")
            if isinstance(constraints, list):
                for constraint in constraints:
                    checkpoints.append(PlanCheckpoint(checkpoint_id=f"checkpoint-{uuid4().hex[:6]}", plan_id=plan_id, stage_id=None, metadata={"constraint": constraint}))
        return stages, dependencies, checkpoints

    def _infer_stage_names(self, goal: str) -> list[str]:
        lowered = goal.lower()
        if "deploy" in lowered:
            return ["Prepare deployment", "Build release", "Deploy service", "Verify deployment"]
        if "test" in lowered or "verify" in lowered:
            return ["Inspect scope", "Create validation plan", "Execute validation", "Report findings"]
        if "research" in lowered or "analy" in lowered:
            return ["Gather context", "Analyze requirements", "Summarize findings", "Recommend next steps"]
        if "build" in lowered or "implement" in lowered:
            return ["Design approach", "Implement changes", "Validate behavior", "Document outcome"]
        return ["Understand goal", "Create implementation steps", "Execute work", "Validate outcome"]

    def _normalize_metadata(self, metadata: dict[str, object] | None) -> dict[str, object]:
        return dict(metadata or {})

    def _coerce_state(self, state: PlanState | str | None, default: PlanState) -> PlanState:
        if isinstance(state, PlanState):
            return state
        if isinstance(state, str):
            try:
                return PlanState(state)
            except ValueError:
                return default
        return default

    def _persist_plan(self, plan: Plan) -> None:
        payload = {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "state": plan.state.value,
            "stages": [
                {"stage_id": s.stage_id, "name": s.name, "status": s.status, "metadata": s.metadata} for s in plan.stages
            ],
            "dependencies": [
                {"dependency_id": d.dependency_id, "target": d.target, "depends_on": d.depends_on} for d in plan.dependencies
            ],
            "checkpoints": [
                {"checkpoint_id": c.checkpoint_id, "plan_id": c.plan_id, "stage_id": c.stage_id, "metadata": c.metadata}
                for c in plan.checkpoints
            ],
            "metadata": plan.metadata,
        }
        metadata = MemoryMetadata(namespace="planning", created_by="PlanningManager", tags=["plan", plan.plan_id])
        record = MemoryRecord(
            record_id=plan.plan_id,
            entries=[
                MemoryEntry(
                    entry_id=str(uuid4()),
                    type=MemoryType.WORKING,
                    content={"kind": "plan", "data": payload},
                    metadata=metadata,
                )
            ],
            namespace="planning",
            metadata=metadata,
        )
        self._memory.store(plan.plan_id, record)

    def _hydrate_from_memory(self) -> None:
        records = self._memory.list_with_filter("planning")
        for record in records:
            try:
                payload = self._extract_payload(record)
                if payload.get("plan_id") is None:
                    continue
                plan = Plan(
                    plan_id=payload["plan_id"],
                    goal=payload["goal"],
                    state=PlanState(payload.get("state", "draft")),
                    stages=tuple(
                        PlanStage(
                            stage_id=s["stage_id"], name=s["name"], status=s.get("status", "pending"), metadata=s.get("metadata", {})
                        )
                        for s in payload.get("stages", [])
                    ),
                    dependencies=tuple(
                        PlanDependency(
                            dependency_id=d["dependency_id"], target=d["target"], depends_on=d["depends_on"]
                        )
                        for d in payload.get("dependencies", [])
                    ),
                    checkpoints=tuple(
                        PlanCheckpoint(
                            checkpoint_id=c["checkpoint_id"],
                            plan_id=c["plan_id"],
                            stage_id=c.get("stage_id"),
                            metadata=c.get("metadata", {}),
                        )
                        for c in payload.get("checkpoints", [])
                    ),
                    metadata=payload.get("metadata", {}),
                )
                with self._lock:
                    self._plans[plan.plan_id] = plan
            except Exception:
                continue

    def _extract_payload(self, record: MemoryRecord) -> dict[str, Any]:
        for entry in record.entries:
            if isinstance(entry.content, dict) and entry.content.get("data") is not None:
                return entry.content.get("data", {})
        return {}

    def _emit_plan_event(self, event_name: str, payload: dict[str, Any]) -> None:
        canonical_name = event_name
        if event_name == "plan_created":
            canonical_name = "plan.created"
        elif event_name == "plan_updated":
            canonical_name = "plan.updated"
        elif event_name == "plan_started":
            canonical_name = "plan.started"
        elif event_name == "plan_completed":
            canonical_name = "plan.completed"
        elif event_name == "plan_failed":
            canonical_name = "plan.failed"
        elif event_name == "plan_cancelled":
            canonical_name = "plan.cancelled"
        elif event_name == "plan_paused":
            canonical_name = "plan.paused"
        elif event_name == "task_added":
            canonical_name = "plan.stage_added"
        elif event_name == "task_completed":
            canonical_name = "plan.stage_completed"
        self._emit_event(canonical_name, payload)
        self._emit_event(event_name, payload)

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload)
        except Exception:
            pass
        try:
            if self._observability_manager:
                self._observability_manager.event_recorder.record({"event": event_name, "payload": payload})
        except Exception:
            pass

    def _audit(self, event: str, identity: str, metadata: dict[str, Any]) -> None:
        try:
            if self._security_manager:
                audit_mgr = self._security_manager.get_audit_manager()
                audit_mgr.record_event(event, identity, self._sanitize_payload(metadata))
        except Exception:
            pass

    def _ensure_permission(self, permission_id: str) -> None:
        try:
            if self._security_manager:
                perm_mgr = self._security_manager.get_permission_manager()
                if not perm_mgr.has_permission("system", permission_id):
                    raise PermissionError(f"Permission denied: {permission_id}")
        except PermissionError:
            raise
        except Exception:
            pass

    def _sanitize_payload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized = {}
        for key, value in metadata.items():
            if key.lower() in {"password", "token", "secret", "api_key"}:
                sanitized[key] = "[redacted]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            else:
                sanitized[key] = value
        return sanitized
