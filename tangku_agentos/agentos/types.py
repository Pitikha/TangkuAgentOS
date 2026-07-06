from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Mapping, Optional, Protocol

AgentId = str
AgentName = str
AgentType = str
AgentVersion = str
AgentMetadata = Dict[str, Any]
AgentPayload = Dict[str, Any]
AgentMessagePayload = Dict[str, Any]
AgentTaskPayload = Dict[str, Any]
AgentResultPayload = Dict[str, Any]
Timestamp = float
Priority = int


class AgentOutputHandler(Protocol):
    def __call__(self, result: "AgentResult") -> None:
        ...


@dataclass(frozen=True)
class AgentDescriptor:
    agent_id: AgentId
    name: AgentName
    agent_type: AgentType
    version: AgentVersion = "0.1.0"
    metadata: AgentMetadata = field(default_factory=dict)


@dataclass
class AgentContext:
    agent_id: AgentId
    name: AgentName
    agent_type: AgentType
    version: AgentVersion = "0.1.0"
    metadata: AgentMetadata = field(default_factory=dict)
    permissions: list["AgentPermission"] = field(default_factory=list)
    capabilities: list["AgentCapability"] = field(default_factory=list)
    registry: Any = field(default_factory=dict)
    state: AgentPayload = field(default_factory=dict)
    configuration: Mapping[str, Any] = field(default_factory=dict)
    shared_context: AgentPayload = field(default_factory=dict)
    runtime_metadata: AgentMetadata = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResourceBudget:
    cpu_budget: float = 0.0
    memory_budget: int = 0
    token_budget: int = 0
    time_budget_seconds: float = 0.0


@dataclass(frozen=True)
class AgentResourceAllocation:
    allocation_id: str
    agent_id: AgentId
    cpu_reserved: float = 0.0
    memory_reserved: int = 0
    token_reserved: int = 0
    time_reserved_seconds: float = 0.0
    metadata: AgentMetadata = field(default_factory=dict)


@dataclass(frozen=True)
class AgentSessionInfo:
    session_id: str
    agent_id: AgentId
    metadata: AgentMetadata = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True


@dataclass(frozen=True)
class AgentMessageRef:
    message_id: str
    sender_id: AgentId
    receiver_id: AgentId


@dataclass(frozen=True)
class AgentTaskMetadata:
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: AgentMetadata = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResultRef:
    task_id: str
    agent_id: AgentId
    status: str
    metadata: AgentMetadata = field(default_factory=dict)
