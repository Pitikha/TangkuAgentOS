from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ExecutionMode(Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BACKGROUND = "background"
    STREAMING = "streaming"


class ExecutionState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass(frozen=True)
class ExecutionContext:
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.SYNCHRONOUS
    timeout_seconds: int | None = None
    retries: int = 0
    checkpoint_enabled: bool = False
    cancelable: bool = True


@dataclass(frozen=True)
class ExecutionSession:
    session_id: str
    execution_id: str
    model_id: str
    provider_id: str | None = None
    state: ExecutionState = ExecutionState.PENDING
    started_at: str | None = None
    ended_at: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Dict[str, Any] | None = None
    duration_seconds: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionHistory:
    session_id: str
    execution_id: str
    result: ExecutionResult
    checkpoint_id: str | None = None
    resumed_from: str | None = None


@dataclass(frozen=True)
class ExecutionRecovery:
    checkpoint_id: str
    session_id: str
    saved_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
