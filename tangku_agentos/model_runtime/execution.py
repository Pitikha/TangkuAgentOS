from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import ModelRequest, ModelResponse, ModelResult, ModelUsage


class ExecutionMode(Enum):
    SYNC = 'sync'
    ASYNC = 'async'
    BACKGROUND = 'background'


@dataclass
class ExecutionContext:
    request_id: str
    mode: ExecutionMode = ExecutionMode.SYNC
    timeout_seconds: int | None = None
    retries: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionSession:
    session_id: str
    request_id: str
    status: str = 'active'
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionQueue:
    queue_id: str
    requests: list[ModelRequest] = field(default_factory=list)


@dataclass
class ExecutionHistory:
    history_id: str
    responses: list[ModelResponse] = field(default_factory=list)


class ExecutionManager:
    """Coordinate execution lifecycle state without performing provider communication."""

    def __init__(self) -> None:
        self._sessions: dict[str, ExecutionSession] = {}
        self._queues: dict[str, ExecutionQueue] = {}
        self._history: dict[str, ExecutionHistory] = {}

    def create_session(self, session_id: str, request_id: str) -> ExecutionSession:
        session = ExecutionSession(session_id=session_id, request_id=request_id)
        self._sessions[session_id] = session
        return session

    def enqueue(self, queue_id: str, request: ModelRequest) -> None:
        queue = self._queues.setdefault(queue_id, ExecutionQueue(queue_id=queue_id))
        queue.requests.append(request)

    def dequeue(self, queue_id: str) -> ModelRequest | None:
        queue = self._queues.get(queue_id)
        if queue is None or not queue.requests:
            return None
        return queue.requests.pop(0)

    def record_response(self, history_id: str, response: ModelResponse) -> None:
        history = self._history.setdefault(history_id, ExecutionHistory(history_id=history_id))
        history.responses.append(response)

    def get_history(self, history_id: str) -> ExecutionHistory | None:
        return self._history.get(history_id)
