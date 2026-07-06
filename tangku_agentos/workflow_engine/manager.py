from __future__ import annotations

import copy
import uuid
from datetime import datetime
from threading import RLock
from typing import Any, Dict, Optional

from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .exceptions import WorkflowManagerError
from .interfaces import (
    WorkflowContextProvider,
    WorkflowEventManager,
    WorkflowExecutor,
    WorkflowHistoryManager,
    WorkflowLifecycleManager,
    WorkflowManagerInterface,
    WorkflowQueue,
    WorkflowRegistryInterface,
)
from .models import Workflow, WorkflowConfiguration, WorkflowEdge, WorkflowInstance, WorkflowMetadata, WorkflowNode, WorkflowState
from .registry import WorkflowRegistry


class _DefaultStateManager:
    def transition(self, instance: WorkflowInstance, state: WorkflowState) -> None:
        return None


class _DefaultHistoryManager:
    def record(self, instance: WorkflowInstance, event: str, payload: dict[str, Any]) -> None:
        return None


class _DefaultEventManager:
    def publish(self, event_name: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        return None


class _DefaultContextProvider:
    def build_context(self, instance: WorkflowInstance) -> dict[str, Any]:
        return {}


class _DefaultQueue:
    def enqueue(self, instance: WorkflowInstance) -> None:
        return None


class _DefaultExecutor:
    def execute(self, instance: WorkflowInstance) -> Any:
        return type("ExecutionResult", (), {"status": WorkflowState.COMPLETED})()


class WorkflowManager(WorkflowManagerInterface):
    """Workflow manager that orchestrates lifecycle, history, and execution."""

    def __init__(
        self,
        registry: WorkflowRegistryInterface | None = None,
        state_manager: WorkflowLifecycleManager | None = None,
        history_manager: WorkflowHistoryManager | None = None,
        event_manager: WorkflowEventManager | None = None,
        context_provider: WorkflowContextProvider | None = None,
        queue: WorkflowQueue | None = None,
        executor: WorkflowExecutor | None = None,
    ) -> None:
        self._registry = registry or WorkflowRegistry()
        self._state_manager = state_manager or _DefaultStateManager()
        self._history_manager = history_manager or _DefaultHistoryManager()
        self._event_manager = event_manager or _DefaultEventManager()
        self._context_provider = context_provider or _DefaultContextProvider()
        self._queue = queue or _DefaultQueue()
        self._executor = executor or _DefaultExecutor()
        self._instances: Dict[str, WorkflowInstance] = {}
        self._lock = RLock()
        self._memory = MemoryManager()

    def create_workflow(self, workflow: Workflow) -> None:
        with self._lock:
            if workflow.workflow_id in {w.workflow_id for w in self._registry.list()}:
                raise WorkflowManagerError(f"Workflow already exists: {workflow.workflow_id}")
            self._registry.register(workflow)
            self._persist_workflow(workflow)
            self._publish_event("workflow.created", {"workflow_id": workflow.workflow_id})

    def update_workflow(self, workflow: Workflow) -> None:
        with self._lock:
            self._registry.unregister(workflow.workflow_id)
            self._registry.register(workflow)
            self._persist_workflow(workflow)
            self._publish_event("workflow.updated", {"workflow_id": workflow.workflow_id})

    def delete_workflow(self, workflow_id: str) -> None:
        with self._lock:
            self._registry.unregister(workflow_id)
            self._publish_event("workflow.deleted", {"workflow_id": workflow_id})

    def clone_workflow(self, workflow_id: str, *, new_id: str | None = None) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        clone = Workflow(
            workflow_id=new_id or f"{workflow.workflow_id}-clone",
            name=f"{workflow.name} (clone)",
            description=workflow.description,
            metadata=workflow.metadata,
            configuration=workflow.configuration,
            stages=copy.deepcopy(workflow.stages),
            nodes=copy.deepcopy(workflow.nodes),
            edges=copy.deepcopy(workflow.edges),
            triggers=copy.deepcopy(workflow.triggers),
            actions=copy.deepcopy(workflow.actions),
        )
        self.create_workflow(clone)
        return clone

    def validate_workflow(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        issues: list[str] = []
        execution_mode = workflow.configuration.execution_mode.value if hasattr(workflow.configuration.execution_mode, "value") else str(workflow.configuration.execution_mode)
        if not workflow.nodes:
            issues.append("workflow requires at least one node")
        if execution_mode == "sequential" and len(workflow.nodes) > 1 and not workflow.edges:
            issues.append("sequential workflow requires edges")
        return {"valid": not issues, "issues": issues, "workflow_id": workflow_id}

    def list_workflows(self) -> list[Workflow]:
        return self._registry.list()

    def list_instances(self) -> list[WorkflowInstance]:
        with self._lock:
            return list(self._instances.values())

    def execute_workflow(self, workflow_id: str, *, inputs: dict[str, Any] | None = None) -> WorkflowInstance:
        workflow = self.get_workflow(workflow_id)
        instance_id = f"{workflow.workflow_id}-{uuid.uuid4().hex}"
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow=workflow,
            state=WorkflowState.READY,
            context=dict(inputs or {}),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        context = self._context_provider.build_context(instance)
        if context is None:
            instance.context = dict(instance.context)
        elif isinstance(context, dict):
            instance.context = dict(context)
        else:
            instance.context = getattr(context, "data", {})

        with self._lock:
            self._instances[instance.instance_id] = instance

        self._persist_instance(instance)
        self._publish_event("workflow.started", {"workflow_id": workflow.workflow_id, "instance_id": instance.instance_id})
        self._history_manager.record(instance, "started", {"workflow_id": workflow.workflow_id})
        self._queue.enqueue(instance)

        result = self._executor.execute(instance)
        self._transition_instance_state(instance, result.status)
        self._history_manager.record(instance, "completed", {"status": result.status.value})
        self._publish_event(
            "workflow.completed" if result.status == WorkflowState.COMPLETED else "workflow.failed",
            {"workflow_id": workflow.workflow_id, "instance_id": instance.instance_id, "status": result.status.value},
        )
        return instance

    def start_workflow(self, workflow_id: str) -> WorkflowInstance:
        return self.execute_workflow(workflow_id)

    def stop_workflow(self, workflow_id: str) -> None:
        instance = self._find_instance(workflow_id)
        self._transition_instance_state(instance, WorkflowState.CANCELLED)
        self._history_manager.record(instance, "stopped", {})
        self._publish_event("workflow.cancelled", {"instance_id": instance.instance_id})

    def pause_workflow(self, workflow_id: str) -> None:
        instance = self._find_instance(workflow_id)
        if instance.state != WorkflowState.RUNNING:
            raise WorkflowManagerError("Agent must be running to pause.")
        self._transition_instance_state(instance, WorkflowState.PAUSED)
        self._history_manager.record(instance, "paused", {})
        self._publish_event("workflow.paused", {"instance_id": instance.instance_id})

    def resume_workflow(self, workflow_id: str) -> None:
        instance = self._find_instance(workflow_id)
        if instance.state != WorkflowState.PAUSED:
            raise WorkflowManagerError("Workflow must be paused to resume.")
        self._transition_instance_state(instance, WorkflowState.RUNNING)
        self._history_manager.record(instance, "resumed", {})
        self._publish_event("workflow.resumed", {"instance_id": instance.instance_id})

    def cancel_workflow(self, workflow_id: str) -> None:
        instance = self._find_instance(workflow_id)
        self._transition_instance_state(instance, WorkflowState.CANCELLED)
        self._history_manager.record(instance, "cancelled", {})
        self._publish_event("workflow.cancelled", {"instance_id": instance.instance_id})

    def archive_workflow(self, workflow_id: str) -> None:
        instance = self._find_instance(workflow_id)
        self._transition_instance_state(instance, WorkflowState.ARCHIVED)
        self._history_manager.record(instance, "archived", {})
        self._publish_event("workflow.archived", {"instance_id": instance.instance_id})

    def get_workflow(self, workflow_id: str) -> Workflow:
        return self._registry.get(workflow_id)

    def _find_instance(self, workflow_id: str) -> WorkflowInstance:
        with self._lock:
            instance = self._instances.get(workflow_id)
            if instance is not None:
                return instance
            for current in self._instances.values():
                if current.workflow.workflow_id == workflow_id:
                    return current
        raise WorkflowManagerError(f"Workflow instance not found: {workflow_id}")

    def _transition_instance_state(self, instance: WorkflowInstance, state: WorkflowState) -> None:
        self._state_manager.transition(instance, state)
        instance.updated_at = datetime.utcnow().isoformat()
        self._persist_instance(instance)

    def _persist_workflow(self, workflow: Workflow) -> None:
        payload = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "metadata": {
                "name": workflow.metadata.name,
                "description": workflow.metadata.description,
                "created_by": workflow.metadata.created_by,
                "version": workflow.metadata.version,
                "tags": workflow.metadata.tags,
                "labels": workflow.metadata.labels,
            },
            "configuration": {
                "execution_mode": workflow.configuration.execution_mode.value,
                "retry_policy": workflow.configuration.retry_policy.value,
                "max_retries": workflow.configuration.max_retries,
                "checkpoint_enabled": workflow.configuration.checkpoint_enabled,
                "rollback_enabled": workflow.configuration.rollback_enabled,
                "schedule_cron": workflow.configuration.schedule_cron,
                "allow_parallel_steps": workflow.configuration.allow_parallel_steps,
            },
            "nodes": [{"node_id": node.node_id, "name": node.name, "label": node.label, "metadata": node.metadata} for node in workflow.nodes],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "source_node_id": edge.source_node_id,
                    "target_node_id": edge.target_node_id,
                    "condition": None if edge.condition is None else {"expression": edge.condition.expression, "metadata": edge.condition.metadata},
                    "metadata": edge.metadata,
                }
                for edge in workflow.edges
            ],
            "stages": [{"stage_id": stage.stage_id, "name": stage.name, "steps": [], "metadata": stage.metadata} for stage in workflow.stages],
        }
        metadata = MemoryMetadata(namespace="workflow", created_by="WorkflowManager", tags=["workflow", workflow.workflow_id])
        record = MemoryRecord(
            record_id=workflow.workflow_id,
            entries=[MemoryEntry(entry_id=str(uuid.uuid4()), type=MemoryType.WORKING, content={"kind": "workflow", "data": payload}, metadata=metadata)],
            namespace="workflow",
            metadata=metadata,
        )
        self._memory.store(workflow.workflow_id, record)

    def _persist_instance(self, instance: WorkflowInstance) -> None:
        payload = {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow.workflow_id,
            "state": instance.state.value,
            "context": instance.context,
            "metadata": instance.metadata,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
        }
        metadata = MemoryMetadata(namespace="workflow", created_by="WorkflowManager", tags=["workflow_instance", instance.instance_id])
        record = MemoryRecord(
            record_id=instance.instance_id,
            entries=[MemoryEntry(entry_id=str(uuid.uuid4()), type=MemoryType.WORKING, content={"kind": "workflow_instance", "data": payload}, metadata=metadata)],
            namespace="workflow",
            metadata=metadata,
        )
        self._memory.store(instance.instance_id, record)

    def _publish_event(self, event_name: str, payload: dict[str, str]) -> None:
        try:
            self._event_manager.publish(event_name, payload)
        except Exception:
            pass
