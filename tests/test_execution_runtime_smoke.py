from tangku_agentos.execution_runtime import (
    ArtifactManager,
    EnvironmentManager,
    ExecutionManager,
    ExecutionQueueManager,
    ResourceManager,
    SandboxManager,
)


def test_execution_runtime_smoke() -> None:
    execution_manager = ExecutionManager()
    sandbox_manager = SandboxManager()
    environment_manager = EnvironmentManager()
    resource_manager = ResourceManager()
    queue_manager = ExecutionQueueManager()
    artifact_manager = ArtifactManager()

    execution_id = execution_manager.execute("task-1", {"script": "echo hi"})
    sandbox_id = sandbox_manager.create_sandbox("sandbox-1", {"workspace": "demo"})
    environment_id = environment_manager.create_environment("dev", {"mode": "isolated"})
    resource_manager.reserve("task-1", {"cpu": 1, "memory": 256})
    queue_manager.enqueue("task-1", {"priority": "normal"})
    artifact_manager.store_artifact("task-1", {"kind": "log"})

    assert execution_manager.get_status(execution_id)["state"] == "completed"
    assert sandbox_manager.get_status(sandbox_id)["workspace"] == "demo"
    assert environment_manager.get_status(environment_id)["mode"] == "isolated"
    assert resource_manager.get_reservation("task-1")["cpu"] == 1
    assert queue_manager.peek()["execution_id"] == "task-1"
    assert artifact_manager.get_artifact("task-1")["kind"] == "log"

    print("execution runtime checks passed")
