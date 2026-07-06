from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CoordinationPolicy(str, Enum):
    LEADER_FOLLOWER = "leader_follower"
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    COMMITTEE = "committee"


@dataclass(slots=True)
class CoordinationMessage:
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: str = "message"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    priority: int = 0
    workflow_id: str | None = None
    session_id: str | None = None
    execution_context: dict[str, Any] = field(default_factory=dict)
    expires_at: datetime | None = None
    status: str = "sent"
    acknowledged: bool = False
    retries: int = 0
    parent_message_id: str | None = None
    routing_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class CoordinationTask:
    task_id: str
    description: str = ""
    agent_id: str | None = None
    status: str = "pending"
    priority: int = 0
    timeout_seconds: int | None = None
    dependencies: list[str] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class DelegationRecord:
    delegation_id: str
    source_agent_id: str
    target_agent_id: str
    delegation_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class CollaborationSession:
    session_id: str
    participants: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class ConflictRecord:
    subject: str
    participants: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class DistributionDecision:
    task_id: str
    agent_id: str
    priority: int = 0
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CoordinationMessage",
    "CoordinationPolicy",
    "CollaborationSession",
    "ConflictRecord",
    "DelegationRecord",
    "DistributionDecision",
]
