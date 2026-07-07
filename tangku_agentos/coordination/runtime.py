from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from tangku_agentos.agent_framework import BaseSpecializedAgent
from tangku_agentos.agentos.messages import AgentMessage, AgentTask
from tangku_agentos.context_engine.manager import ContextManager
from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.knowledge_engine.manager import KnowledgeManager
from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType
from tangku_agentos.planning_runtime.manager import PlanningManager
from tangku_agentos.provider_runtime.manager import ProviderManager
from tangku_agentos.provider_runtime.registry import ProviderRegistry
from tangku_agentos.reasoning_runtime.manager import ReasoningManager
from tangku_agentos.terminal_runtime.manager import CommandManager, CommandRequest, TerminalManager
from tangku_agentos.workflow_engine import (
    Workflow,
    WorkflowConfiguration,
    WorkflowContextManager,
    WorkflowEdge,
    WorkflowEventManagerImpl,
    WorkflowExecutorImpl,
    WorkflowHistoryManagerImpl,
    WorkflowManager,
    WorkflowMetadata,
    WorkflowNode,
    WorkflowQueue,
    WorkflowRegistry,
    WorkflowStateManager,
)
from tangku_agentos.workflow_engine.models import ExecutionMode
from tangku_agentos.workspace_engine.manager import WorkspaceManager

from .models import (
    CollaborationSession,
    ConflictRecord,
    CoordinationMessage,
    CoordinationPolicy,
    DelegationRecord,
    DistributionDecision,
)


class MultiAgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseSpecializedAgent] = {}
        self._groups: dict[str, list[str]] = defaultdict(list)
        self._lock = RLock()

    def register(self, agent: BaseSpecializedAgent, group_id: str | None = None) -> None:
        with self._lock:
            self._agents[agent.descriptor.agent_id] = agent
            if group_id:
                self._groups[group_id].append(agent.descriptor.agent_id)

    def discover(self, group_id: str | None = None) -> list[BaseSpecializedAgent]:
        with self._lock:
            if group_id is None:
                return list(self._agents.values())
            agent_ids = self._groups.get(group_id, [])
            return [self._agents[agent_id] for agent_id in agent_ids if agent_id in self._agents]

    def get(self, agent_id: str) -> BaseSpecializedAgent | None:
        with self._lock:
            return self._agents.get(agent_id)


class MultiAgentMessageBus:
    def __init__(self) -> None:
        self._history: list[CoordinationMessage] = []
        self._subscriptions: dict[str, list[Callable[[CoordinationMessage], None]]] = defaultdict(list)
        self._lock = RLock()

    def direct_message(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        return self._record_message(
            CoordinationMessage(
                message_id=f"msg-{sender_id}-{recipient_id}",
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type="direct",
                payload=payload,
                metadata=metadata or {},
                correlation_id=metadata.get("correlation_id") if metadata else None,
                priority=int(metadata.get("priority", 0)) if metadata else 0,
                workflow_id=metadata.get("workflow_id") if metadata else None,
                session_id=metadata.get("session_id") if metadata else None,
                execution_context=metadata.get("execution_context", {}) if metadata else {},
                expires_at=metadata.get("expires_at") if metadata else None,
                routing_key=metadata.get("routing_key") if metadata else None,
            )
        )

    def broadcast(self, sender_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[CoordinationMessage]:
        message = self._record_message(
            CoordinationMessage(
                message_id=f"broadcast-{sender_id}",
                sender_id=sender_id,
                recipient_id="*",
                message_type="broadcast",
                payload=payload,
                metadata=metadata or {},
                correlation_id=metadata.get("correlation_id") if metadata else None,
                priority=int(metadata.get("priority", 0)) if metadata else 0,
                workflow_id=metadata.get("workflow_id") if metadata else None,
                session_id=metadata.get("session_id") if metadata else None,
                execution_context=metadata.get("execution_context", {}) if metadata else {},
                expires_at=metadata.get("expires_at") if metadata else None,
                routing_key=metadata.get("routing_key") if metadata else None,
            )
        )
        return [message]

    def multicast(self, sender_id: str, recipient_ids: list[str], payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[CoordinationMessage]:
        messages = []
        for recipient_id in recipient_ids:
            messages.append(self.direct_message(sender_id, recipient_id, payload, metadata=metadata))
        return messages

    def request_response(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "request")
        message = self.direct_message(sender_id, recipient_id, {"request": payload}, metadata=metadata)
        message.metadata.setdefault("response_expected", True)
        return message

    def reply(self, parent_message: CoordinationMessage, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("parent_message_id", parent_message.message_id)
        metadata.setdefault("correlation_id", parent_message.correlation_id or parent_message.message_id)
        return self.direct_message(sender_id, recipient_id, {"reply": payload}, metadata=metadata)

    def acknowledge(self, parent_message: CoordinationMessage, sender_id: str, recipient_id: str, metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("parent_message_id", parent_message.message_id)
        metadata.setdefault("correlation_id", parent_message.correlation_id or parent_message.message_id)
        message = self.direct_message(sender_id, recipient_id, {"ack": True}, metadata=metadata)
        message.status = "acknowledged"
        return message

    def notification(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "notification")
        return self.direct_message(sender_id, recipient_id, payload, metadata=metadata)

    def event(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "event")
        return self.direct_message(sender_id, recipient_id, {"event": payload}, metadata=metadata)

    def progress(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "progress")
        return self.direct_message(sender_id, recipient_id, {"progress": payload}, metadata=metadata)

    def error(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "error")
        return self.direct_message(sender_id, recipient_id, {"error": payload}, metadata=metadata)

    def heartbeat(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "heartbeat")
        return self.direct_message(sender_id, recipient_id, {"heartbeat": payload}, metadata=metadata)

    def completion(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationMessage:
        metadata = dict(metadata or {})
        metadata.setdefault("message_type", "completion")
        return self.direct_message(sender_id, recipient_id, {"completion": payload}, metadata=metadata)

    def subscribe(self, routing_key: str, callback: Callable[[CoordinationMessage], None]) -> None:
        with self._lock:
            self._subscriptions[routing_key].append(callback)

    def unsubscribe(self, routing_key: str, callback: Callable[[CoordinationMessage], None]) -> None:
        with self._lock:
            self._subscriptions.get(routing_key, [])
            self._subscriptions[routing_key] = [subscriber for subscriber in self._subscriptions.get(routing_key, []) if subscriber is not callback]

    def replay(self, *, correlation_id: str | None = None, recipient_id: str | None = None, sender_id: str | None = None, message_type: str | None = None) -> list[CoordinationMessage]:
        with self._lock:
            matches = []
            for message in self._history:
                if correlation_id is not None and message.correlation_id != correlation_id:
                    continue
                if recipient_id is not None and message.recipient_id != recipient_id:
                    continue
                if sender_id is not None and message.sender_id != sender_id:
                    continue
                if message_type is not None and message.message_type != message_type:
                    continue
                matches.append(message)
            return matches

    def filter(self, predicate: Callable[[CoordinationMessage], bool]) -> list[CoordinationMessage]:
        with self._lock:
            return [message for message in self._history if predicate(message)]

    def history(self) -> list[CoordinationMessage]:
        with self._lock:
            return list(self._history)

    def _record_message(self, message: CoordinationMessage) -> CoordinationMessage:
        if not message.correlation_id:
            message.correlation_id = f"corr-{message.message_id}"
        with self._lock:
            self._history.append(message)
            for routing_key, subscribers in list(self._subscriptions.items()):
                if routing_key in {message.routing_key, message.message_type, message.recipient_id, "*"}:
                    for subscriber in subscribers:
                        subscriber(message)
        return message


class MultiAgentDelegationManager:
    def __init__(self) -> None:
        self._history: list[DelegationRecord] = []
        self._lock = RLock()

    def delegate_task(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        record = DelegationRecord(delegation_id=f"delegation-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, delegation_type="task", payload=payload, metadata=metadata or {})
        with self._lock:
            self._history.append(record)
        return record

    def delegate_workflow(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        record = DelegationRecord(delegation_id=f"workflow-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, delegation_type="workflow", payload=payload, metadata=metadata or {})
        with self._lock:
            self._history.append(record)
        return record

    def delegate_capability(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        record = DelegationRecord(delegation_id=f"capability-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, delegation_type="capability", payload=payload, metadata=metadata or {})
        with self._lock:
            self._history.append(record)
        return record

    def delegate_tool(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        record = DelegationRecord(delegation_id=f"tool-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, delegation_type="tool", payload=payload, metadata=metadata or {})
        with self._lock:
            self._history.append(record)
        return record

    def delegate_goal(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        record = DelegationRecord(delegation_id=f"goal-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, delegation_type="goal", payload=payload, metadata=metadata or {})
        with self._lock:
            self._history.append(record)
        return record

    def history(self) -> list[DelegationRecord]:
        with self._lock:
            return list(self._history)


class MultiAgentSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, CollaborationSession] = {}
        self._lock = RLock()

    def create_session(self, session_id: str, participants: list[str] | None = None) -> CollaborationSession:
        with self._lock:
            session = CollaborationSession(session_id=session_id, participants=participants or [])
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> CollaborationSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> list[CollaborationSession]:
        with self._lock:
            return list(self._sessions.values())


class MultiAgentContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def get_context(self, context_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._contexts.setdefault(context_id, {}))

    def update_context(self, context_id: str, updates: dict[str, Any]) -> None:
        with self._lock:
            self._contexts.setdefault(context_id, {}).update(updates)


class MultiAgentLifecycleManager:
    def __init__(self) -> None:
        self._running = False
        self._lock = RLock()

    def start(self) -> None:
        with self._lock:
            self._running = True

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def is_running(self) -> bool:
        with self._lock:
            return self._running


class MultiAgentConfigurationManager:
    def __init__(self) -> None:
        self._config: dict[str, Any] = {"policy": "peer_to_peer"}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value


class MultiAgentMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, Any]] = {}

    def set(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)


class MultiAgentStatisticsManager:
    def __init__(self) -> None:
        self._stats: dict[str, int] = {"messages": 0, "delegations": 0, "sessions": 0, "agents": 0}

    def record(self, key: str, value: int = 1) -> None:
        self._stats[key] = self._stats.get(key, 0) + value

    def snapshot(self) -> dict[str, int]:
        return dict(self._stats)


class MultiAgentHealthManager:
    def __init__(self) -> None:
        self._status = "ready"
        self._agent_metrics: dict[str, dict[str, Any]] = {}
        self._heartbeats: dict[str, datetime] = {}

    def status(self) -> str:
        return self._status

    def mark(self, status: str) -> None:
        self._status = status

    def record_heartbeat(self, agent_id: str, *, status: str = "healthy", metrics: dict[str, Any] | None = None) -> None:
        self._heartbeats[agent_id] = datetime.now(timezone.utc)
        snapshot = {"status": status, "last_heartbeat": self._heartbeats[agent_id].isoformat()}
        if metrics:
            snapshot.update(metrics)
        self._agent_metrics[agent_id] = snapshot

    def snapshot(self) -> dict[str, Any]:
        return {"status": self._status, "agents": dict(self._agent_metrics), "heartbeats": {agent_id: timestamp.isoformat() for agent_id, timestamp in self._heartbeats.items()}}


class CollaborationManager:
    def __init__(self) -> None:
        self._sessions: dict[str, CollaborationSession] = {}

    def create_session(self, session_id: str, participants: list[str] | None = None) -> CollaborationSession:
        session = CollaborationSession(session_id=session_id, participants=participants or [])
        self._sessions[session_id] = session
        return session


class SharedContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}

    def get_context(self, context_id: str) -> dict[str, Any]:
        return dict(self._contexts.setdefault(context_id, {}))

    def update_context(self, context_id: str, updates: dict[str, Any]) -> None:
        self._contexts.setdefault(context_id, {}).update(updates)


class SharedMemoryCoordinator:
    def __init__(self) -> None:
        self._memory: dict[str, Any] = {}
        self._versions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._locks: dict[str, str] = {}

    def store(self, key: str, value: Any) -> None:
        self._memory[key] = value
        self._versions[key].append({"value": value, "timestamp": datetime.now(timezone.utc).isoformat()})

    def retrieve(self, key: str) -> Any:
        return self._memory.get(key)

    def get_versions(self, key: str) -> list[dict[str, Any]]:
        return list(self._versions.get(key, []))

    def lock(self, key: str, owner_id: str) -> bool:
        if key in self._locks:
            return False
        self._locks[key] = owner_id
        return True

    def unlock(self, key: str) -> None:
        self._locks.pop(key, None)

    def list_keys(self) -> list[str]:
        return sorted(self._memory.keys())


class SharedKnowledgeCoordinator:
    def __init__(self) -> None:
        self._knowledge: dict[str, Any] = {}

    def index(self, key: str, value: Any) -> None:
        self._knowledge[key] = value

    def retrieve(self, key: str) -> Any:
        return self._knowledge.get(key)


class SharedWorkspaceCoordinator:
    def __init__(self) -> None:
        self._workspace: dict[str, Any] = {}

    def update(self, key: str, value: Any) -> None:
        self._workspace[key] = value

    def get(self, key: str) -> Any:
        return self._workspace.get(key)


class SharedWorkflowCoordinator:
    def __init__(self) -> None:
        self._workflows: dict[str, Any] = {}

    def register(self, workflow_id: str, workflow: Any) -> None:
        self._workflows[workflow_id] = workflow

    def get(self, workflow_id: str) -> Any:
        return self._workflows.get(workflow_id)


class CoordinationPolicyManager:
    def __init__(self) -> None:
        self._policies: dict[str, CoordinationPolicy] = {}

    def set_policy(self, session_id: str, policy: CoordinationPolicy) -> None:
        self._policies[session_id] = policy

    def resolve_policy(self, session_id: str) -> CoordinationPolicy | None:
        return self._policies.get(session_id)


class ConflictManager:
    def __init__(self) -> None:
        self._history: list[ConflictRecord] = []

    def record_conflict(self, subject: str, participants: list[str], metadata: dict[str, Any] | None = None) -> ConflictRecord:
        record = ConflictRecord(subject=subject, participants=participants, metadata=metadata or {})
        self._history.append(record)
        return record

    def history(self) -> list[ConflictRecord]:
        return list(self._history)


class LockManager:
    def __init__(self) -> None:
        self._locks: dict[str, str] = {}

    def acquire(self, resource_id: str, owner_id: str) -> bool:
        if resource_id in self._locks:
            return False
        self._locks[resource_id] = owner_id
        return True

    def release(self, resource_id: str) -> None:
        self._locks.pop(resource_id, None)


class ResourceCoordinator:
    def __init__(self) -> None:
        self._resources: dict[str, str] = {}

    def claim(self, resource_id: str, owner_id: str) -> bool:
        if resource_id in self._resources:
            return False
        self._resources[resource_id] = owner_id
        return True


class OwnershipRegistry:
    def __init__(self) -> None:
        self._owners: dict[str, str] = {}

    def register(self, resource_id: str, owner_id: str) -> None:
        self._owners[resource_id] = owner_id


class WorkDistributor:
    def __init__(self) -> None:
        self._last: list[DistributionDecision] = []

    def distribute(self, task_id: str, agents: list[BaseSpecializedAgent], capabilities: list[str] | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> list[DistributionDecision]:
        decisions = [DistributionDecision(task_id=task_id, agent_id=agent.descriptor.agent_id, priority=priority, capabilities=capabilities or [], metadata=metadata or {}) for agent in agents]
        self._last = decisions
        return decisions


class SchedulingCoordinator:
    def __init__(self) -> None:
        self._queue: list[dict[str, Any]] = []
        self._running: dict[str, dict[str, Any]] = {}
        self._completed: set[str] = set()
        self._failed: dict[str, dict[str, Any]] = {}
        self._retry_queue: list[dict[str, Any]] = []
        self._dead_letter_queue: list[dict[str, Any]] = []

    def schedule(self, task_id: str, priority: int = 0, dependencies: list[str] | None = None, retries: int = 0, timeout: int | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        task = {
            "task_id": task_id,
            "priority": priority,
            "dependencies": list(dependencies or []),
            "retries": retries,
            "timeout": timeout,
            "metadata": metadata or {},
            "status": "pending",
        }
        self._queue.append(task)
        self._queue.sort(key=lambda item: (-item["priority"], item["task_id"]))
        return task

    def mark_running(self, task_id: str) -> None:
        for task in self._queue:
            if task["task_id"] == task_id:
                task["status"] = "running"
                self._running[task_id] = task
                break

    def mark_completed(self, task_id: str) -> None:
        self._completed.add(task_id)
        self._running.pop(task_id, None)
        for task in self._queue:
            if task["task_id"] == task_id:
                task["status"] = "completed"
                break

    def mark_failed(self, task_id: str, error: str | None = None) -> None:
        self._failed[task_id] = {"task_id": task_id, "error": error or "failed"}
        self._running.pop(task_id, None)
        for task in self._queue:
            if task["task_id"] == task_id:
                task["status"] = "failed"
                break

    def retry(self, task_id: str) -> dict[str, Any] | None:
        task = None
        for queue_task in self._queue:
            if queue_task["task_id"] == task_id:
                task = dict(queue_task)
                task["status"] = "retry"
                task["retries"] = max(0, task.get("retries", 0) - 1)
                self._retry_queue.append(task)
                break
        return task

    def dead_letter(self, task_id: str, error: str | None = None) -> dict[str, Any] | None:
        task = None
        for queue_task in self._queue:
            if queue_task["task_id"] == task_id:
                task = dict(queue_task)
                task["status"] = "dead_letter"
                task["error"] = error or "dead_letter"
                self._dead_letter_queue.append(task)
                break
        return task

    def cancel(self, task_id: str) -> None:
        self._queue = [task for task in self._queue if task["task_id"] != task_id]
        self._running.pop(task_id, None)

    def get_ready_tasks(self, completed_task_ids: set[str] | None = None) -> list[dict[str, Any]]:
        completed_task_ids = completed_task_ids or self._completed
        ready = []
        for task in self._queue:
            if task["status"] in {"running", "completed", "failed", "dead_letter"}:
                continue
            if all(dependency in completed_task_ids for dependency in task.get("dependencies", [])):
                ready.append(task)
        ready.sort(key=lambda item: (-item["priority"], item["task_id"]))
        return ready

    def snapshot(self) -> dict[str, Any]:
        return {
            "pending": [task for task in self._queue if task["status"] == "pending"],
            "running": list(self._running.values()),
            "completed": list(self._completed),
            "failed": list(self._failed.keys()),
            "retry_queue": self._retry_queue,
            "dead_letter_queue": self._dead_letter_queue,
        }


class LoadDistributionManager:
    def __init__(self) -> None:
        self._loads: dict[str, int] = {}

    def record(self, agent_id: str, value: int) -> None:
        self._loads[agent_id] = self._loads.get(agent_id, 0) + value

    def distribute(self, task_id: str, agents: list[BaseSpecializedAgent], capabilities: list[str] | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> list[DistributionDecision]:
        decisions = [
            DistributionDecision(
                task_id=task_id,
                agent_id=agent.descriptor.agent_id,
                priority=priority,
                capabilities=capabilities or [],
                metadata=metadata or {},
            )
            for agent in agents
        ]
        return decisions


class AgentAvailabilityManager:
    def __init__(self) -> None:
        self._availability: dict[str, bool] = {}

    def set_available(self, agent_id: str, available: bool) -> None:
        self._availability[agent_id] = available

    def is_available(self, agent_id: str) -> bool:
        return self._availability.get(agent_id, True)


class AgentCapabilityMatcher:
    def __init__(self) -> None:
        self._last: list[str] = []

    def match(self, agent: BaseSpecializedAgent, capabilities: list[str]) -> bool:
        agent_capabilities = {capability.name for capability in agent.capabilities}
        return any(capability in agent_capabilities for capability in capabilities)


class MultiAgentManager:
    def __init__(self, *, event_bus: EventBus | None = None, security_manager: Any | None = None, observability_manager: Any | None = None) -> None:
        self.registry = MultiAgentRegistry()
        self.session_manager = MultiAgentSessionManager()
        self.context_manager = MultiAgentContextManager()
        self.lifecycle_manager = MultiAgentLifecycleManager()
        self.configuration_manager = MultiAgentConfigurationManager()
        self.metadata_manager = MultiAgentMetadataManager()
        self.statistics_manager = MultiAgentStatisticsManager()
        self.health_manager = MultiAgentHealthManager()
        self.message_bus = MultiAgentMessageBus()
        self.delegation_manager = MultiAgentDelegationManager()
        self.collaboration_manager = CollaborationManager()
        self.shared_context_manager = SharedContextManager()
        self.shared_memory = SharedMemoryCoordinator()
        self.shared_knowledge = SharedKnowledgeCoordinator()
        self.shared_workspace = SharedWorkspaceCoordinator()
        self.shared_workflow = SharedWorkflowCoordinator()
        self.policy_manager = CoordinationPolicyManager()
        self.conflict_manager = ConflictManager()
        self.lock_manager = LockManager()
        self.resource_coordinator = ResourceCoordinator()
        self.ownership_registry = OwnershipRegistry()
        self.work_distributor = WorkDistributor()
        self.scheduling_coordinator = SchedulingCoordinator()
        self.load_distribution_manager = LoadDistributionManager()
        self.distribution_manager = self.load_distribution_manager
        self.availability_manager = AgentAvailabilityManager()
        self.capability_matcher = AgentCapabilityMatcher()
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._memory = MemoryManager()
        self._planning_manager = PlanningManager(event_bus=self._event_bus, security_manager=security_manager, observability_manager=observability_manager)
        self._reasoning_manager = ReasoningManager(event_bus=self._event_bus, security_manager=security_manager, observability_manager=observability_manager)
        self._context_engine = ContextManager(event_bus=self._event_bus, security_manager=security_manager, observability_manager=observability_manager)
        self._knowledge_engine = KnowledgeManager(event_bus=self._event_bus, security_manager=security_manager, observability_manager=observability_manager)
        self._provider_manager = ProviderManager(registry=ProviderRegistry())
        self._workflow_manager = WorkflowManager(
            registry=WorkflowRegistry(),
            state_manager=WorkflowStateManager(),
            history_manager=WorkflowHistoryManagerImpl(),
            event_manager=WorkflowEventManagerImpl(),
            context_provider=WorkflowContextManager(),
            queue=WorkflowQueue(),
            executor=WorkflowExecutorImpl(),
        )
        self._terminal_manager = TerminalManager()
        self._workspace_manager = WorkspaceManager(security_manager=security_manager, observability_manager=observability_manager, event_bus=self._event_bus)
        self._command_manager = CommandManager(security_manager=security_manager, observability_manager=observability_manager)
        self._agent_states: dict[str, str] = {}
        self._agent_contexts: dict[str, dict[str, Any]] = {}
        self._task_queue: list[dict[str, Any]] = []
        self._agent_sessions: dict[str, Any] = {}

    def register_agent(self, agent: BaseSpecializedAgent, group_id: str | None = None) -> None:
        self.registry.register(agent, group_id)
        self.statistics_manager.record("agents")
        self.availability_manager.set_available(agent.descriptor.agent_id, True)
        self._agent_states[agent.descriptor.agent_id] = "registered"
        self.health_manager.record_heartbeat(agent.descriptor.agent_id, status="healthy", metrics={"queue_size": 0, "active_jobs": 0})
        self._emit_event("agent.registered", {"agent_id": agent.descriptor.agent_id, "group_id": group_id})

    def discover_agents(self, group_id: str | None = None) -> list[BaseSpecializedAgent]:
        return self.registry.discover(group_id)

    def create_session(self, session_id: str, participants: list[str] | None = None, metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.session.create")
        session = self.collaboration_manager.create_session(session_id, participants=participants)
        if metadata:
            session.metadata.update(metadata)
        self.session_manager._sessions[session_id] = session
        self._agent_sessions[session_id] = session
        self.statistics_manager.record("sessions")
        self._emit_event("agent.session.created", {"session_id": session_id, "participants": participants or []})
        return session

    def send_message(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.message.send")
        message = self.message_bus.direct_message(sender_id, recipient_id, payload, metadata=metadata)
        self.statistics_manager.record("messages")
        self._emit_event("agent.message.sent", {"sender_id": sender_id, "recipient_id": recipient_id, "payload": payload})
        return message

    def broadcast_message(self, sender_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[Any]:
        self._ensure_permission("agent.message.broadcast")
        messages = self.message_bus.broadcast(sender_id, payload, metadata=metadata)
        self.statistics_manager.record("messages")
        return messages

    def multicast_message(self, sender_id: str, recipient_ids: list[str], payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[Any]:
        self._ensure_permission("agent.message.multicast")
        messages = self.message_bus.multicast(sender_id, recipient_ids, payload, metadata=metadata)
        self.statistics_manager.record("messages", len(messages))
        return messages

    def publish(self, event_name: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        self._event_bus.publish(event_name, payload, metadata=metadata)

    def request_response(self, sender_id: str, recipient_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.message.request")
        return self.message_bus.request_response(sender_id, recipient_id, payload, metadata=metadata)

    def share_context(self, context_id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_permission("agent.context.share")
        self.shared_context_manager.update_context(context_id, data)
        self._agent_contexts[context_id] = data
        self._emit_event("agent.context.shared", {"context_id": context_id, "data": data})
        return {"shared": True, "context_id": context_id, "data": data}

    def share_memory(self, key: str, value: Any) -> Any:
        self._ensure_permission("agent.memory.share")
        self.shared_memory.store(key, value)
        metadata = MemoryMetadata(namespace="multi_agent", created_by="MultiAgentManager", tags=["shared_memory", key])
        record = MemoryRecord(
            record_id=key,
            entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "shared_memory", "data": value}, metadata=metadata)],
            namespace="multi_agent",
            metadata=metadata,
        )
        self._memory.store(key, record)
        self._emit_event("agent.memory.shared", {"key": key, "value": value})
        return value

    def share_knowledge(self, key: str, value: Any) -> Any:
        self._ensure_permission("agent.knowledge.share")
        self.shared_knowledge.index(key, value)
        try:
            self._knowledge_engine.create_entity(entity_type="shared_knowledge", name=key, metadata={"value": value})
        except Exception:
            pass
        self._emit_event("agent.knowledge.shared", {"key": key, "value": value})
        return value

    def share_workspace(self, key: str, value: Any) -> Any:
        self._ensure_permission("agent.workspace.share")
        self.shared_workspace.update(key, value)
        return value

    def create_plan(self, goal: str, *, agent_id: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        self._ensure_permission("agent.plan.create")
        plan_id = self._planning_manager.create_plan(goal, metadata={**(metadata or {}), "agent_id": agent_id})
        self._emit_event("agent.plan.created", {"plan_id": plan_id, "agent_id": agent_id})
        return plan_id

    def modify_plan(self, plan_id: str, *, goal: str | None = None, metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.plan.update")
        return self._planning_manager.update_plan(plan_id, goal=goal, metadata=metadata)

    def execute_plan(self, plan_id: str) -> Any:
        self._ensure_permission("agent.plan.execute")
        return self._planning_manager.execute_plan(plan_id)

    def delegate_task(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.delegation.create")
        record = self.delegation_manager.delegate_task(source_agent_id, target_agent_id, payload, metadata=metadata)
        self._emit_event("agent.delegation.created", {"source_agent_id": source_agent_id, "target_agent_id": target_agent_id, "payload": payload})
        return record

    def delegate_plan_stage(self, plan_id: str, source_agent_id: str, target_agent_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_permission("agent.plan.delegate")
        self._emit_event("agent.plan.stage.delegated", {"plan_id": plan_id, "source_agent_id": source_agent_id, "target_agent_id": target_agent_id})
        return {"plan_id": plan_id, "source_agent_id": source_agent_id, "target_agent_id": target_agent_id, "delegated": True, "payload": payload or {}}

    def create_reasoning_session(self, session_id: str, *, agent_id: str | None = None, metadata: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.reasoning.create")
        context_id = f"reasoning-{session_id}"
        session = self._reasoning_manager.create_session(context_id, metadata={**(metadata or {}), "agent_id": agent_id})
        self._emit_event("agent.reasoning.started", {"session_id": session.session_id, "agent_id": agent_id})
        return session

    def share_reasoning_trace(self, session_id: str, trace_data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_permission("agent.reasoning.share")
        self._emit_event("agent.reasoning.shared", {"session_id": session_id, "trace_data": trace_data})
        return {"session_id": session_id, "trace_data": trace_data}

    def explain_decision(self, session_id: str, query: str, context_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._reasoning_manager.explain(session_id, query, context_data=context_data)

    def compare_solutions(self, session_id: str, solutions: list[dict[str, Any]]) -> dict[str, Any]:
        self._ensure_permission("agent.reasoning.compare")
        return {"session_id": session_id, "solutions": solutions, "compared": True}

    def merge_reasoning(self, session_id: str, traces: list[dict[str, Any]]) -> dict[str, Any]:
        self._ensure_permission("agent.reasoning.merge")
        return {"session_id": session_id, "merged": True, "traces": traces}

    def schedule_task(self, task_id: str, *, priority: int = 0, dependencies: list[str] | None = None, retries: int = 0, timeout: int | None = None) -> dict[str, Any]:
        self._ensure_permission("agent.scheduler.schedule")
        task = self.scheduling_coordinator.schedule(task_id, priority=priority, dependencies=dependencies, retries=retries, timeout=timeout)
        self._task_queue.append(task)
        self._emit_event("agent.task.scheduled", task)
        return task

    def execute_parallel(self, agent_ids: list[str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_permission("agent.execution.parallel")
        results: list[dict[str, Any]] = []
        for agent_id in agent_ids:
            agent = self.registry.get(agent_id)
            if agent is None:
                continue
            if hasattr(agent, "execute_task"):
                task = AgentTask(task_id=f"task-{agent_id}", agent_id=agent_id, payload=payload or {})
                result = agent.execute_task(task)
                results.append({"agent_id": agent_id, "status": getattr(result, "status", None).value if hasattr(getattr(result, "status", None), "value") else getattr(result, "status", None)})
            else:
                results.append({"agent_id": agent_id, "status": "handled"})
        return {"status": "completed", "results": results}

    def get_runtime_metrics(self) -> dict[str, Any]:
        return {
            "messages": self.statistics_manager.snapshot(),
            "health": self.health_manager.snapshot(),
            "scheduler": self.scheduling_coordinator.snapshot(),
            "shared_memory_keys": self.shared_memory.list_keys(),
            "agent_count": len(self.registry.discover()),
        }

    def recover(self) -> dict[str, Any]:
        self.health_manager.mark("recovering")
        self._emit_event("runtime.recovering", {})
        return {"status": "recovered", "metrics": self.get_runtime_metrics()}

    def trigger_workflow(self, workflow_id: str, *, inputs: dict[str, Any] | None = None) -> Any:
        self._ensure_permission("agent.workflow.trigger")
        try:
            workflow = self._workflow_manager.get_workflow(workflow_id)
        except Exception:
            workflow = Workflow(
                workflow_id=workflow_id,
                name=workflow_id,
                metadata=WorkflowMetadata(version="1.0"),
                configuration=WorkflowConfiguration(execution_mode=ExecutionMode.SEQUENTIAL),
                nodes=[WorkflowNode(node_id=f"{workflow_id}-start", name="start")],
                edges=[WorkflowEdge(source_node_id=f"{workflow_id}-start", target_node_id=f"{workflow_id}-start")],
            )
            self._workflow_manager.create_workflow(workflow)
        return self._workflow_manager.execute_workflow(workflow_id, inputs=inputs or {})

    def schedule_workflow(self, workflow_id: str, cron_expression: str) -> dict[str, Any]:
        self._ensure_permission("agent.workflow.schedule")
        return {"workflow_id": workflow_id, "scheduled": True, "cron_expression": cron_expression}

    def trigger_automation(self, automation_id: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_permission("agent.automation.trigger")
        return {"automation_id": automation_id, "status": "triggered", "payload": payload or {}}

    def read_file(self, workspace_id: str, relative_path: str) -> str:
        self._ensure_permission("agent.workspace.read")
        workspace = self._workspace_manager.get_workspace(workspace_id)
        if workspace is None:
            return ""
        path = self._workspace_manager._workspace_root(workspace) / relative_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_file(self, workspace_id: str, relative_path: str, content: str) -> Any:
        self._ensure_permission("agent.workspace.write")
        return self._workspace_manager.create_file(workspace_id, relative_path, content)

    def modify_repository(self, workspace_id: str, relative_path: str, content: str) -> Any:
        self._ensure_permission("agent.workspace.modify")
        return self.write_file(workspace_id, relative_path, content)

    def execute_terminal_command(self, command: str, args: list[str] | None = None, cwd: str | None = None, timeout: float | None = None) -> Any:
        self._ensure_permission("agent.terminal.execute")
        request = CommandRequest(request_id=str(uuid4()), command=command, args=args or [], cwd=cwd, environment={}, metadata={"timeout": timeout})
        return self._command_manager.create_command(request)

    def select_provider(self, provider_id: str, configuration: Any) -> Any:
        self._ensure_permission("agent.provider.select")
        self._provider_manager.add_provider(provider_id, configuration)
        return self._provider_manager.get_provider(provider_id)

    def pause_agent(self, agent_id: str) -> bool:
        self._ensure_permission("agent.lifecycle.pause")
        agent = self.registry.get(agent_id)
        if agent is None:
            return False
        if hasattr(agent, "pause"):
            try:
                agent.pause()
            except Exception:
                self._agent_states[agent_id] = "paused"
                self._emit_event("agent.paused", {"agent_id": agent_id})
                return True
        self._agent_states[agent_id] = "paused"
        self._emit_event("agent.paused", {"agent_id": agent_id})
        return True

    def resume_agent(self, agent_id: str) -> bool:
        self._ensure_permission("agent.lifecycle.resume")
        agent = self.registry.get(agent_id)
        if agent is None:
            return False
        if hasattr(agent, "resume"):
            try:
                agent.resume()
            except Exception:
                self._agent_states[agent_id] = "running"
                self._emit_event("agent.resumed", {"agent_id": agent_id})
                return True
        self._agent_states[agent_id] = "running"
        self._emit_event("agent.resumed", {"agent_id": agent_id})
        return True

    def stop_agent(self, agent_id: str) -> bool:
        self._ensure_permission("agent.lifecycle.stop")
        agent = self.registry.get(agent_id)
        if agent is None:
            return False
        if hasattr(agent, "stop"):
            try:
                agent.stop()
            except Exception:
                self._agent_states[agent_id] = "stopped"
                self._emit_event("agent.stopped", {"agent_id": agent_id})
                return True
        self._agent_states[agent_id] = "stopped"
        self._emit_event("agent.stopped", {"agent_id": agent_id})
        return True

    def restart_agent(self, agent_id: str) -> bool:
        self._ensure_permission("agent.lifecycle.restart")
        agent = self.registry.get(agent_id)
        if agent is None:
            return False
        if hasattr(agent, "restart"):
            try:
                agent.restart()
            except Exception:
                self._agent_states[agent_id] = "running"
                self._emit_event("agent.restarted", {"agent_id": agent_id})
                return True
        self._agent_states[agent_id] = "running"
        self._emit_event("agent.restarted", {"agent_id": agent_id})
        return True

    def get_agent_state(self, agent_id: str) -> str:
        return self._agent_states.get(agent_id, "unknown")

    def start_runtime(self) -> None:
        self.lifecycle_manager.start()
        self.health_manager.mark("running")
        self._emit_event("runtime.started", {})

    def stop_runtime(self) -> None:
        self.lifecycle_manager.stop()
        self.health_manager.mark("stopped")
        self._emit_event("runtime.stopped", {})

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload)
        except Exception:
            pass
        try:
            if self._observability_manager and hasattr(self._observability_manager, "event_recorder"):
                self._observability_manager.event_recorder.record({"event": event_name, "payload": payload})
        except Exception:
            pass

    def _ensure_permission(self, permission_id: str) -> None:
        if self._security_manager is None:
            return
        try:
            perm_mgr = self._security_manager.get_permission_manager()
            if not perm_mgr.has_permission("system", permission_id):
                raise PermissionError(f"Permission denied: {permission_id}")
        except PermissionError:
            raise
        except Exception:
            pass

    def get_agent_profiles(self) -> list[dict[str, Any]]:
        agents = self.registry.discover()
        profiles = []
        for agent in agents:
            profiles.append(
                {
                    "agent_id": agent.descriptor.agent_id,
                    "name": agent.profile.name,
                    "role": agent.profile.role,
                    "description": agent.profile.description,
                    "version": agent.profile.version,
                    "tags": list(agent.profile.tags),
                    "capabilities": [getattr(capability, "name", str(capability)) for capability in agent.capabilities],
                    "status": getattr(agent, "state", "unknown").value if hasattr(getattr(agent, "state", None), "value") else getattr(agent, "state", str(agent.state)),
                    "health": {
                        "status": getattr(agent.health, "status", "unknown"),
                        "message": getattr(agent.health, "message", ""),
                        "details": getattr(agent.health, "details", {}),
                        "last_updated": getattr(agent.health, "last_updated", None),
                    },
                    "metadata": getattr(agent, "metadata", {}).to_dict() if hasattr(getattr(agent, "metadata", {}), "to_dict") else dict(getattr(agent, "metadata", {})),
                    "context": {
                        "agent_id": agent.context.agent_id,
                        "name": agent.context.name,
                        "agent_type": agent.context.agent_type,
                        "metadata": getattr(agent.context, "metadata", {}),
                    },
                }
            )
        return profiles

    def select_agents_by_capabilities(self, capabilities: list[str]) -> list[BaseSpecializedAgent]:
        agents = self.registry.discover()
        return [agent for agent in agents if self.capability_matcher.match(agent, capabilities)]

    def distribute_task(self, task_id: str, capabilities: list[str] | None = None, target_agent_id: str | None = None, priority: int = 0, metadata: dict[str, Any] | None = None) -> list[DistributionDecision]:
        agents = self.registry.discover()
        if target_agent_id:
            agent = self.registry.get(target_agent_id)
            if agent:
                agents = [agent]
            else:
                agents = []
        elif capabilities:
            agents = self.select_agents_by_capabilities(capabilities)
        decisions = self.work_distributor.distribute(task_id=task_id, agents=agents, capabilities=capabilities or [], priority=priority, metadata=metadata)
        for decision in decisions:
            self.statistics_manager.record("delegations")
            self._emit_event("agent.task.distributed", {"task_id": task_id, "agent_id": decision.agent_id, "capabilities": decision.capabilities})
        return decisions

    def list_agents(self) -> list[dict[str, Any]]:
        return self.get_agent_profiles()


__all__ = [
    "AgentAvailabilityManager",
    "AgentCapabilityMatcher",
    "CollaborationManager",
    "ConflictManager",
    "CoordinationPolicyManager",
    "LoadDistributionManager",
    "LockManager",
    "MultiAgentConfigurationManager",
    "MultiAgentContextManager",
    "MultiAgentDelegationManager",
    "MultiAgentHealthManager",
    "MultiAgentLifecycleManager",
    "MultiAgentManager",
    "MultiAgentMessageBus",
    "MultiAgentMetadataManager",
    "MultiAgentRegistry",
    "MultiAgentSessionManager",
    "MultiAgentStatisticsManager",
    "OwnershipRegistry",
    "ResourceCoordinator",
    "SchedulingCoordinator",
    "SharedContextManager",
    "SharedKnowledgeCoordinator",
    "SharedMemoryCoordinator",
    "SharedWorkflowCoordinator",
    "SharedWorkspaceCoordinator",
    "WorkDistributor",
]
