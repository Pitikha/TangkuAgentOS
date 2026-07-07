from __future__ import annotations

import os
import subprocess
from threading import RLock
from typing import Any, Dict, List

from .models import (
    CommandContext,
    CommandHistory,
    CommandMetadata,
    CommandRequest,
    CommandResult,
    EnvironmentProfile,
    PipelineContext,
    PipelineHistory,
    PipelineMetadata,
    ProcessContext,
    ProcessLifecycle,
    ProcessMetadata,
    ProcessState,
    RuntimeEnvironment,
    StreamBuffer,
    TerminalConfiguration,
    TerminalContext,
    TerminalHealth,
    TerminalLifecycle,
    TerminalMetadata,
    TerminalProfile,
    TerminalSession,
    TerminalStatistics,
)


class TerminalManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, TerminalSession] = {}
        self._contexts: Dict[str, TerminalContext] = {}
        self._configurations: Dict[str, TerminalConfiguration] = {}
        self._metadata: Dict[str, TerminalMetadata] = {}
        self._statistics: Dict[str, TerminalStatistics] = {}
        self._health: Dict[str, TerminalHealth] = {}
        self._lifecycles: Dict[str, TerminalLifecycle] = {}
        self._profiles: Dict[str, TerminalProfile] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

    def create_session(self, session_id: str, profile_id: str | None = None, metadata: dict[str, Any] | None = None) -> TerminalSession:
        with self._lock:
            session = TerminalSession(session_id=session_id, profile_id=profile_id, metadata=metadata or {})
            self._sessions[session_id] = session
            self._contexts[session_id] = TerminalContext(session_id=session_id, cwd=None, environment={}, metadata=metadata or {})
            self._configurations[session_id] = TerminalConfiguration(session_id=session_id)
            self._metadata[session_id] = TerminalMetadata(session_id=session_id, metadata=metadata or {})
            self._statistics[session_id] = TerminalStatistics(session_id=session_id, stats={"commands": 0})
            self._health[session_id] = TerminalHealth(session_id=session_id)
            self._lifecycles[session_id] = TerminalLifecycle(session_id=session_id, state="created")
            self._history[session_id] = []
            return session

    def get_session(self, session_id: str) -> TerminalSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def set_profile(self, profile_id: str, profile: TerminalProfile) -> None:
        with self._lock:
            self._profiles[profile_id] = profile

    def get_profile(self, profile_id: str) -> TerminalProfile | None:
        with self._lock:
            return self._profiles.get(profile_id)

    def list_sessions(self) -> list[TerminalSession]:
        with self._lock:
            return list(self._sessions.values())


class TerminalRegistry:
    def __init__(self) -> None:
        self._sessions: Dict[str, TerminalSession] = {}
        self._lock = RLock()

    def register(self, session: TerminalSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def resolve(self, session_id: str) -> TerminalSession | None:
        with self._lock:
            return self._sessions.get(session_id)


class TerminalSessionManager:
    def __init__(self, terminal_manager: TerminalManager | None = None) -> None:
        self._terminal_manager = terminal_manager or TerminalManager()
        self._lock = RLock()

    def open(self, session_id: str, profile_id: str | None = None, metadata: dict[str, Any] | None = None) -> TerminalSession:
        with self._lock:
            session = self._terminal_manager.create_session(session_id, profile_id=profile_id, metadata=metadata)
            self._terminal_manager._lifecycles[session_id] = TerminalLifecycle(session_id=session_id, state="opened")
            return session

    def close(self, session_id: str) -> None:
        with self._lock:
            self._terminal_manager._lifecycles[session_id] = TerminalLifecycle(session_id=session_id, state="closed")


class TerminalContextManager:
    def __init__(self) -> None:
        self._contexts: Dict[str, TerminalContext] = {}
        self._lock = RLock()

    def update(self, session_id: str, cwd: str | None = None, environment: dict[str, str] | None = None) -> TerminalContext:
        with self._lock:
            context = TerminalContext(session_id=session_id, cwd=cwd, environment=environment or {}, metadata={})
            self._contexts[session_id] = context
            return context


class TerminalLifecycleManager:
    def __init__(self) -> None:
        self._lifecycles: Dict[str, TerminalLifecycle] = {}
        self._lock = RLock()

    def transition(self, session_id: str, state: str) -> TerminalLifecycle:
        with self._lock:
            lifecycle = TerminalLifecycle(session_id=session_id, state=state)
            self._lifecycles[session_id] = lifecycle
            return lifecycle


class TerminalConfigurationManager:
    def __init__(self) -> None:
        self._configurations: Dict[str, TerminalConfiguration] = {}
        self._lock = RLock()

    def set(self, session_id: str, settings: dict[str, Any]) -> TerminalConfiguration:
        with self._lock:
            configuration = TerminalConfiguration(session_id=session_id, settings=settings)
            self._configurations[session_id] = configuration
            return configuration


class TerminalMetadataManager:
    def __init__(self) -> None:
        self._metadata: Dict[str, TerminalMetadata] = {}
        self._lock = RLock()

    def set(self, session_id: str, metadata: dict[str, Any]) -> TerminalMetadata:
        with self._lock:
            terminal_metadata = TerminalMetadata(session_id=session_id, metadata=metadata)
            self._metadata[session_id] = terminal_metadata
            return terminal_metadata


class TerminalStatisticsManager:
    def __init__(self) -> None:
        self._stats: Dict[str, TerminalStatistics] = {}
        self._lock = RLock()

    def record(self, session_id: str, key: str, value: Any) -> TerminalStatistics:
        with self._lock:
            stats = self._stats.get(session_id, TerminalStatistics(session_id=session_id, stats={}))
            new_stats = dict(stats.stats)
            new_stats[key] = value
            terminal_stats = TerminalStatistics(session_id=session_id, stats=new_stats)
            self._stats[session_id] = terminal_stats
            return terminal_stats


class TerminalHealthManager:
    def __init__(self) -> None:
        self._health: Dict[str, TerminalHealth] = {}
        self._lock = RLock()

    def set(self, session_id: str, status: str, details: dict[str, Any] | None = None) -> TerminalHealth:
        with self._lock:
            health = TerminalHealth(session_id=session_id, status=status, details=details or {})
            self._health[session_id] = health
            return health


class CommandManager:
    def __init__(self, security_manager: Any | None = None, observability_manager: Any | None = None) -> None:
        self._history: Dict[str, CommandHistory] = {}
        self._contexts: Dict[str, CommandContext] = {}
        self._metadata: Dict[str, CommandMetadata] = {}
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._lock = RLock()

    def create_command(self, request: CommandRequest) -> CommandResult:
        context = CommandContext(request_id=request.request_id, cwd=request.cwd, environment=request.environment)
        with self._lock:
            self._contexts[request.request_id] = context
            self._metadata[request.request_id] = CommandMetadata(request_id=request.request_id, command=request.command)

        result = self.execute(request, timeout=request.metadata.get("timeout"))

        with self._lock:
            self._history[request.request_id] = CommandHistory(
                request_id=request.request_id,
                entries=[{"command": request.command, "args": list(request.args), "result": result.metadata}],
            )

        if self._security_manager is not None:
            audit_manager = getattr(self._security_manager, "get_audit_manager", None)
            if callable(audit_manager):
                audit_manager().record_event(
                    "terminal_command_executed",
                    request.request_id,
                    metadata={"command": request.command, "exit_code": result.exit_code},
                )

        if self._observability_manager is not None:
            event_recorder = getattr(self._observability_manager, "event_recorder", None)
            if event_recorder is not None and hasattr(event_recorder, "record"):
                event_recorder.record(
                    type("Event", (), {"timeline_id": request.request_id, "events": [{"event": "command-executed", "request_id": request.request_id}], "metadata": {"command": request.command}})()
                )

        return result

    def execute(self, request: CommandRequest, timeout: float | None = None) -> CommandResult:
        environment = os.environ.copy()
        environment.update(request.environment or {})
        cwd = request.cwd or os.getcwd()
        try:
            completed = subprocess.run(
                [request.command, *request.args],
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return CommandResult(
                request_id=request.request_id,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                metadata={"command": request.command, "cwd": cwd, "environment": dict(request.environment), "timeout": timeout},
            )
        except subprocess.TimeoutExpired as exc:
            timeout_message = f"Command timed out after {timeout}s"
            stderr = (exc.stderr or "")
            if stderr:
                stderr = f"{stderr}\n{timeout_message}"
            else:
                stderr = timeout_message
            return CommandResult(
                request_id=request.request_id,
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=stderr,
                metadata={"command": request.command, "cwd": cwd, "environment": dict(request.environment), "timeout": timeout},
            )
        except FileNotFoundError as exc:
            return CommandResult(
                request_id=request.request_id,
                exit_code=127,
                stdout="",
                stderr=str(exc),
                metadata={"command": request.command, "cwd": cwd, "environment": dict(request.environment), "timeout": timeout},
            )
        except OSError as exc:
            return CommandResult(
                request_id=request.request_id,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                metadata={"command": request.command, "cwd": cwd, "environment": dict(request.environment), "timeout": timeout},
            )


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: Dict[str, CommandMetadata] = {}
        self._lock = RLock()

    def register(self, request: CommandRequest) -> CommandMetadata:
        with self._lock:
            metadata = CommandMetadata(request_id=request.request_id, command=request.command, metadata={"args": list(request.args)})
            self._commands[request.request_id] = metadata
            return metadata


class ProcessManager:
    def __init__(self) -> None:
        self._processes: Dict[str, ProcessContext] = {}
        self._metadata: Dict[str, ProcessMetadata] = {}
        self._lifecycles: Dict[str, ProcessLifecycle] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

    def register(self, process_id: str, parent_id: str | None = None, metadata: dict[str, Any] | None = None) -> ProcessContext:
        with self._lock:
            context = ProcessContext(process_id=process_id, parent_id=parent_id, state=ProcessState.CREATED, metadata=metadata or {})
            self._processes[process_id] = context
            self._metadata[process_id] = ProcessMetadata(process_id=process_id, owner="system", metadata=metadata or {})
            self._lifecycles[process_id] = ProcessLifecycle(process_id=process_id, state=ProcessState.CREATED)
            self._history[process_id] = []
            return context

    def transition(self, process_id: str, state: ProcessState) -> ProcessLifecycle:
        with self._lock:
            lifecycle = ProcessLifecycle(process_id=process_id, state=state)
            self._lifecycles[process_id] = lifecycle
            return lifecycle


class ProcessRegistry:
    def __init__(self) -> None:
        self._processes: Dict[str, ProcessContext] = {}
        self._lock = RLock()

    def register(self, process: ProcessContext) -> None:
        with self._lock:
            self._processes[process.process_id] = process


class StreamManager:
    def __init__(self) -> None:
        self._buffers: Dict[str, StreamBuffer] = {}
        self._lock = RLock()

    def write(self, stream_id: str, chunk: str) -> StreamBuffer:
        with self._lock:
            buffer = self._buffers.get(stream_id, StreamBuffer(stream_id=stream_id))
            chunks = list(buffer.chunks) + [chunk]
            self._buffers[stream_id] = StreamBuffer(stream_id=stream_id, chunks=chunks)
            return self._buffers[stream_id]

    def read(self, stream_id: str) -> StreamBuffer:
        with self._lock:
            return self._buffers.get(stream_id, StreamBuffer(stream_id=stream_id))


class EnvironmentVariableManager:
    def __init__(self) -> None:
        self._environments: Dict[str, RuntimeEnvironment] = {}
        self._profiles: Dict[str, EnvironmentProfile] = {}
        self._lock = RLock()

    def create_environment(self, environment_id: str, variables: dict[str, str] | None = None, cwd: str | None = None, profile: str | None = None) -> RuntimeEnvironment:
        with self._lock:
            environment = RuntimeEnvironment(environment_id=environment_id, variables=variables or {}, cwd=cwd, profile=profile)
            self._environments[environment_id] = environment
            return environment

    def create_profile(self, profile_id: str, variables: dict[str, str] | None = None, cwd: str | None = None) -> EnvironmentProfile:
        with self._lock:
            profile = EnvironmentProfile(profile_id=profile_id, variables=variables or {}, cwd=cwd)
            self._profiles[profile_id] = profile
            return profile


class EnvironmentRegistry:
    def __init__(self) -> None:
        self._environments: Dict[str, RuntimeEnvironment] = {}
        self._lock = RLock()

    def register(self, environment: RuntimeEnvironment) -> None:
        with self._lock:
            self._environments[environment.environment_id] = environment


class CommandPipelineManager:
    def __init__(self) -> None:
        self._pipelines: Dict[str, PipelineContext] = {}
        self._history: Dict[str, PipelineHistory] = {}
        self._metadata: Dict[str, PipelineMetadata] = {}
        self._lock = RLock()

    def create_pipeline(self, pipeline_id: str, steps: list[str] | None = None, metadata: dict[str, Any] | None = None) -> PipelineContext:
        with self._lock:
            context = PipelineContext(pipeline_id=pipeline_id, steps=tuple(steps or []), metadata=metadata or {})
            self._pipelines[pipeline_id] = context
            self._history[pipeline_id] = PipelineHistory(pipeline_id=pipeline_id, entries=[])
            self._metadata[pipeline_id] = PipelineMetadata(pipeline_id=pipeline_id, metadata=metadata or {})
            return context

    def add_step(self, pipeline_id: str, step: str) -> PipelineContext:
        with self._lock:
            context = self._pipelines.get(pipeline_id, PipelineContext(pipeline_id=pipeline_id))
            steps = list(context.steps) + [step]
            updated = PipelineContext(pipeline_id=pipeline_id, steps=tuple(steps), metadata=context.metadata)
            self._pipelines[pipeline_id] = updated
            return updated
