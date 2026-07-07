from __future__ import annotations

from tangku_agentos.terminal_runtime import (
    CommandManager,
    CommandPipelineManager,
    CommandRequest,
    EnvironmentVariableManager,
    ProcessManager,
    StreamManager,
    TerminalManager,
)


def test_terminal_runtime_smoke() -> None:
    terminal_manager = TerminalManager()
    session = terminal_manager.create_session("session-1", profile_id="default")
    assert session.session_id == "session-1"

    command_manager = CommandManager()
    request = CommandRequest(request_id="cmd-1", command="echo", args=("hello",), environment={"MODE": "test"}, cwd="/tmp")
    result = command_manager.create_command(request)
    assert result.request_id == "cmd-1"

    process_manager = ProcessManager()
    process = process_manager.register("proc-1", parent_id=None, metadata={"owner": "agent"})
    assert process.process_id == "proc-1"

    stream_manager = StreamManager()
    buffer = stream_manager.write("out-1", "hello")
    assert buffer.chunks == ["hello"]

    environment_manager = EnvironmentVariableManager()
    environment = environment_manager.create_environment("env-1", variables={"MODE": "test"}, cwd="/tmp", profile="default")
    assert environment.environment_id == "env-1"

    pipeline_manager = CommandPipelineManager()
    pipeline = pipeline_manager.create_pipeline("pipeline-1", steps=["step-1"], metadata={"mode": "sequential"})
    assert pipeline.pipeline_id == "pipeline-1"


def test_command_manager_executes_processes_and_handles_timeouts() -> None:
    command_manager = CommandManager()

    success_request = CommandRequest(
        request_id="cmd-success",
        command="python3",
        args=("-c", "import sys; print('hello-from-python'); sys.stderr.write('warn-from-python\\n')"),
        cwd="/tmp",
    )
    success_result = command_manager.create_command(success_request)
    assert success_result.exit_code == 0
    assert "hello-from-python" in success_result.stdout
    assert "warn-from-python" in success_result.stderr

    timeout_request = CommandRequest(
        request_id="cmd-timeout",
        command="python3",
        args=("-c", "import time; time.sleep(2)"),
        cwd="/tmp",
    )
    timeout_result = command_manager.execute(timeout_request, timeout=0.2)
    assert timeout_result.exit_code != 0
    assert "timed out" in timeout_result.stderr.lower() or timeout_result.exit_code == 1
