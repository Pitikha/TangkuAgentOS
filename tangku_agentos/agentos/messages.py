from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from .types import AgentMessagePayload, AgentResultPayload, AgentTaskPayload
from .constants import AgentStatus


@dataclass(frozen=True)
class AgentMessage:
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str = "message"
    related_id: str | None = None
    payload: AgentMessagePayload = field(default_factory=dict)
    sent_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent_id: str
    payload: AgentTaskPayload = field(default_factory=dict)
    priority: int = 0
    timeout_seconds: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AgentResult:
    result_id: str
    task_id: str
    agent_id: str
    status: AgentStatus = AgentStatus.PENDING
    payload: AgentResultPayload = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
