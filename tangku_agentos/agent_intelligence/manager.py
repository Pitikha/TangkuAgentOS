from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List

from .models import (
    AgentDefinition,
    AgentMessage,
    AgentMessageEnvelope,
    AgentTask,
    CollaborationPolicy,
    CoordinationRecord,
    DelegationRecord,
    GoalState,
    ProgressSnapshot,
    SharedArtifact,
    Team,
    TeamRole,
)


class AgentManager:
    def __init__(self) -> None:
        self._agents: Dict[str, AgentDefinition] = {}
        self._lock = RLock()

    def register_agent(self, agent_id: str, capabilities: list[str] | None = None, metadata: dict[str, Any] | None = None) -> AgentDefinition:
        with self._lock:
            definition = AgentDefinition(agent_id=agent_id, capabilities=tuple(capabilities or []), metadata=metadata or {})
            self._agents[agent_id] = definition
            return definition

    def get_agent(self, agent_id: str) -> AgentDefinition | None:
        with self._lock:
            return self._agents.get(agent_id)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, AgentDefinition] = {}
        self._lock = RLock()

    def register(self, agent: AgentDefinition) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> AgentDefinition | None:
        with self._lock:
            return self._agents.get(agent_id)


class AgentLifecycleManager:
    def __init__(self) -> None:
        self._states: Dict[str, str] = {}
        self._lock = RLock()

    def transition(self, agent_id: str, state: str) -> None:
        with self._lock:
            self._states[agent_id] = state


class AgentSessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def start(self, agent_id: str, session_id: str | None = None) -> str:
        with self._lock:
            resolved = session_id or f"{agent_id}-session"
            self._sessions[resolved] = {"agent_id": agent_id}
            return resolved


class AgentContextManager:
    def __init__(self) -> None:
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def update(self, context_id: str, values: dict[str, Any]) -> None:
        with self._lock:
            self._contexts[context_id] = {**self._contexts.get(context_id, {}), **values}


class AgentStateManager:
    def __init__(self) -> None:
        self._states: Dict[str, str] = {}
        self._lock = RLock()

    def set(self, agent_id: str, state: str) -> None:
        with self._lock:
            self._states[agent_id] = state


class AgentConfigurationManager:
    def __init__(self) -> None:
        self._configurations: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, agent_id: str, configuration: dict[str, Any]) -> None:
        with self._lock:
            self._configurations[agent_id] = dict(configuration)


class AgentMetadataManager:
    def __init__(self) -> None:
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, agent_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._metadata[agent_id] = dict(metadata)


class AgentStatisticsManager:
    def __init__(self) -> None:
        self._stats: Dict[str, int] = {}
        self._lock = RLock()

    def record(self, agent_id: str, key: str, value: int = 1) -> None:
        with self._lock:
            current = self._stats.get(agent_id, 0)
            self._stats[f"{agent_id}:{key}"] = current + value


class AgentHealthManager:
    def __init__(self) -> None:
        self._health: Dict[str, str] = {}
        self._lock = RLock()

    def set(self, agent_id: str, status: str) -> None:
        with self._lock:
            self._health[agent_id] = status


class WorkflowAgent(AgentDefinition):
    def __init__(self, agent_id: str = "workflow-agent") -> None:
        super().__init__(agent_id=agent_id, agent_type="workflow", capabilities=("workflow",), workflows=("orchestration",))


class AgentCoordinator:
    def __init__(self) -> None:
        self._history: List[DelegationRecord] = []
        self._lock = RLock()

    def delegate(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> DelegationRecord:
        with self._lock:
            record = DelegationRecord(delegation_id=f"delegation-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, payload=payload, metadata=metadata or {})
            self._history.append(record)
            return record


class AgentScheduler:
    def __init__(self) -> None:
        self._queue: List[AgentTask] = []
        self._lock = RLock()

    def schedule(self, task: AgentTask) -> None:
        with self._lock:
            self._queue.append(task)


class AgentDispatcher:
    def __init__(self) -> None:
        self._dispatches: List[CoordinationRecord] = []
        self._lock = RLock()

    def dispatch(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationRecord:
        with self._lock:
            record = CoordinationRecord(record_id=f"coord-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, payload=payload, metadata=metadata or {})
            self._dispatches.append(record)
            return record


class AgentRouter:
    def __init__(self) -> None:
        self._lock = RLock()

    def route(self, capability: str, candidates: list[dict[str, Any]]) -> str | None:
        with self._lock:
            for candidate in candidates:
                if capability in candidate.get("capabilities", []):
                    return candidate["agent_id"]
            return None


class AgentNegotiator:
    def __init__(self) -> None:
        self._history: List[CoordinationRecord] = []
        self._lock = RLock()

    def negotiate(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationRecord:
        with self._lock:
            record = CoordinationRecord(record_id=f"negotiate-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, payload=payload, metadata=metadata or {})
            self._history.append(record)
            return record


class AgentConsensusManager:
    def __init__(self) -> None:
        self._history: List[CoordinationRecord] = []
        self._lock = RLock()

    def reach(self, source_agent_id: str, target_agent_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> CoordinationRecord:
        with self._lock:
            record = CoordinationRecord(record_id=f"consensus-{source_agent_id}-{target_agent_id}", source_agent_id=source_agent_id, target_agent_id=target_agent_id, payload=payload, metadata=metadata or {})
            self._history.append(record)
            return record


class AgentMessageBus:
    def __init__(self) -> None:
        self._history: List[AgentMessage] = []
        self._lock = RLock()

    def send(self, sender_id: str, recipient_id: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> AgentMessage:
        with self._lock:
            message = AgentMessage(message_id=f"msg-{sender_id}-{recipient_id}", sender_id=sender_id, recipient_id=recipient_id, content=content, metadata=metadata or {})
            self._history.append(message)
            return message


class BroadcastManager:
    def __init__(self) -> None:
        self._history: List[AgentMessage] = []
        self._lock = RLock()

    def broadcast(self, sender_id: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> List[AgentMessage]:
        with self._lock:
            message = AgentMessage(message_id=f"broadcast-{sender_id}", sender_id=sender_id, recipient_id="*", content=content, metadata=metadata or {})
            self._history.append(message)
            return [message]


class SharedMemoryManager:
    def __init__(self) -> None:
        self._memory: Dict[str, Any] = {}
        self._lock = RLock()

    def store(self, key: str, value: Any) -> None:
        with self._lock:
            self._memory[key] = value

    def retrieve(self, key: str) -> Any:
        with self._lock:
            return self._memory.get(key)


class SharedContextManager:
    def __init__(self) -> None:
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def update(self, context_id: str, values: dict[str, Any]) -> None:
        with self._lock:
            self._contexts[context_id] = {**self._contexts.get(context_id, {}), **values}


class SharedKnowledgeManager:
    def __init__(self) -> None:
        self._knowledge: Dict[str, Any] = {}
        self._lock = RLock()

    def index(self, key: str, value: Any) -> None:
        with self._lock:
            self._knowledge[key] = value

    def retrieve(self, key: str) -> Any:
        with self._lock:
            return self._knowledge.get(key)


class SharedWorkspaceManager:
    def __init__(self) -> None:
        self._artifacts: Dict[str, SharedArtifact] = {}
        self._lock = RLock()

    def update(self, artifact_id: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> SharedArtifact:
        with self._lock:
            artifact = SharedArtifact(artifact_id=artifact_id, content=content, metadata=metadata or {})
            self._artifacts[artifact_id] = artifact
            return artifact

    def get(self, artifact_id: str) -> SharedArtifact | None:
        with self._lock:
            return self._artifacts.get(artifact_id)


class TeamManager:
    def __init__(self) -> None:
        self._teams: Dict[str, Team] = {}
        self._lock = RLock()

    def create_team(self, team_id: str, members: list[str] | None = None, roles: list[TeamRole] | None = None, metadata: dict[str, Any] | None = None) -> Team:
        with self._lock:
            team = Team(team_id=team_id, members=tuple(members or []), roles=tuple(roles or []), metadata=metadata or {})
            self._teams[team_id] = team
            return team


class TeamRegistry:
    def __init__(self) -> None:
        self._teams: Dict[str, Team] = {}
        self._lock = RLock()

    def register(self, team: Team) -> None:
        with self._lock:
            self._teams[team.team_id] = team


class RoleManager:
    def __init__(self) -> None:
        self._roles: Dict[str, TeamRole] = {}
        self._lock = RLock()

    def add_role(self, role: TeamRole) -> None:
        with self._lock:
            self._roles[role.role_id] = role


class CollaborationPolicyManager:
    def __init__(self) -> None:
        self._policies: Dict[str, CollaborationPolicy] = {}
        self._lock = RLock()

    def set_policy(self, policy_id: str, policy: dict[str, Any]) -> None:
        with self._lock:
            self._policies[policy_id] = CollaborationPolicy(policy_id=policy_id, policy=policy)

    def get_policy(self, policy_id: str) -> dict[str, Any] | None:
        with self._lock:
            policy = self._policies.get(policy_id)
            return None if policy is None else policy.policy


class TaskAssignmentManager:
    def __init__(self) -> None:
        self._assignments: Dict[str, AgentTask] = {}
        self._lock = RLock()

    def assign(self, task: AgentTask) -> None:
        with self._lock:
            self._assignments[task.task_id] = task


class GoalMonitor:
    def __init__(self) -> None:
        self._goals: Dict[str, GoalState] = {}
        self._lock = RLock()

    def track(self, goal_id: str, status: str, progress: float = 0.0, metadata: dict[str, Any] | None = None) -> GoalState:
        with self._lock:
            state = GoalState(goal_id=goal_id, status=status, progress=progress, metadata=metadata or {})
            self._goals[goal_id] = state
            return state

    def get_status(self, goal_id: str) -> str | None:
        with self._lock:
            return self._goals.get(goal_id).status if goal_id in self._goals else None


class ProgressMonitor:
    def __init__(self) -> None:
        self._progress: Dict[str, float] = {}
        self._lock = RLock()

    def update(self, goal_id: str, progress: float) -> None:
        with self._lock:
            self._progress[goal_id] = progress

    def get_progress(self, goal_id: str) -> float | None:
        with self._lock:
            return self._progress.get(goal_id)


class DecisionCoordinator:
    def __init__(self) -> None:
        self._lock = RLock()

    def decide(self, goal_id: str, context: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return {"goal_id": goal_id, "decision": "proceed", "context": context}


class ReflectionManager:
    def __init__(self) -> None:
        self._history: Dict[str, List[str]] = {}
        self._lock = RLock()

    def record(self, goal_id: str, reflection: str) -> None:
        with self._lock:
            self._history.setdefault(goal_id, []).append(reflection)

    def get_history(self, goal_id: str) -> List[str]:
        with self._lock:
            return list(self._history.get(goal_id, []))


class AdaptationManager:
    def __init__(self) -> None:
        self._changes: Dict[str, List[str]] = {}
        self._lock = RLock()

    def record_change(self, goal_id: str, change: str) -> None:
        with self._lock:
            self._changes.setdefault(goal_id, []).append(change)

    def get_changes(self, goal_id: str) -> List[str]:
        with self._lock:
            return list(self._changes.get(goal_id, []))
