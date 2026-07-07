from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ProcessState(Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class CommandRequest:
    request_id: str
    command: str
    args: tuple[str, ...] = ()
    environment: Dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    request_id: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandContext:
    request_id: str
    cwd: str | None = None
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandMetadata:
    request_id: str
    command: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandHistory:
    request_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ProcessContext:
    process_id: str
    parent_id: str | None = None
    state: ProcessState = ProcessState.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessMetadata:
    process_id: str
    owner: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessLifecycle:
    process_id: str
    state: ProcessState = ProcessState.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InputStream:
    stream_id: str
    history: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class OutputStream:
    stream_id: str
    history: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ErrorStream:
    stream_id: str
    history: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class StreamBuffer:
    stream_id: str
    chunks: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeEnvironment:
    environment_id: str
    variables: Dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    profile: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentProfile:
    profile_id: str
    variables: Dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineContext:
    pipeline_id: str
    steps: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineHistory:
    pipeline_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineMetadata:
    pipeline_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalSession:
    session_id: str
    profile_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalConfiguration:
    session_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalContext:
    session_id: str
    cwd: str | None = None
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalMetadata:
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalProfile:
    profile_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalStatistics:
    session_id: str
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalHealth:
    session_id: str
    status: str = "healthy"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TerminalLifecycle:
    session_id: str
    state: str = "created"
    metadata: Dict[str, Any] = field(default_factory=dict)
