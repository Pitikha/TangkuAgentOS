from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    agent_type: str = "generic"
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    workflows: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentMessage:
    message_id: str
    sender_id: str
    recipient_id: str
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentMessageEnvelope:
    message_id: str
    sender_id: str
    recipient_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeamRole:
    role_id: str
    name: str
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class Team:
    team_id: str
    members: tuple[str, ...] = ()
    roles: tuple[TeamRole, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CoordinationRecord:
    record_id: str
    source_agent_id: str
    target_agent_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DelegationRecord:
    delegation_id: str
    source_agent_id: str
    target_agent_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoalState:
    goal_id: str
    status: str = "draft"
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProgressSnapshot:
    goal_id: str
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SharedArtifact:
    artifact_id: str
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CollaborationPolicy:
    policy_id: str
    policy: Dict[str, Any] = field(default_factory=dict)
