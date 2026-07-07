from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import ToolRequest, ToolResponse, ToolResult, ToolStatus


class ExecutionMode(Enum):
    SYNC = 'sync'
    ASYNC = 'async'
    BACKGROUND = 'background'


@dataclass
class ToolExecutionContext:
    request_id: str
    tool_id: str
    mode: ExecutionMode = ExecutionMode.SYNC
    timeout_seconds: int | None = None
    retries: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionSession:
    session_id: str
    tool_id: str
    status: str = 'active'
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionQueue:
    queue_id: str
    items: list[ToolExecutionContext] = field(default_factory=list)


@dataclass
class ToolExecutionHistory:
    history_id: str
    responses: list[ToolResponse] = field(default_factory=list)


class ToolExecutionManager:
    """Coordinate execution lifecycle state without running concrete tools."""

    def __init__(self) -> None:
        self._sessions: dict[str, ToolExecutionSession] = {}
        self._queue: dict[str, ToolExecutionQueue] = {}
        self._history: dict[str, ToolExecutionHistory] = {}

    def create_session(self, session_id: str, tool_id: str) -> ToolExecutionSession:
        session = ToolExecutionSession(session_id=session_id, tool_id=tool_id)
        self._sessions[session_id] = session
        return session

    def enqueue(self, queue_id: str, context: ToolExecutionContext) -> None:
        queue = self._queue.setdefault(queue_id, ToolExecutionQueue(queue_id=queue_id))
        queue.items.append(context)

    def dequeue(self, queue_id: str) -> ToolExecutionContext | None:
        queue = self._queue.get(queue_id)
        if queue is None or not queue.items:
            return None
        return queue.items.pop(0)

    def record_response(self, history_id: str, response: ToolResponse) -> None:
        history = self._history.setdefault(history_id, ToolExecutionHistory(history_id=history_id))
        history.responses.append(response)

    def get_history(self, history_id: str) -> ToolExecutionHistory | None:
        return self._history.get(history_id)
