from __future__ import annotations

from tangku_agentos.kernel_runtime import (
    KernelBootstrap,
    KernelConfiguration,
    KernelContext,
    KernelHealth,
    KernelLifecycle,
    KernelManager,
    KernelMetadata,
    KernelRuntime,
    KernelStatistics,
    ResourceManager,
    RuntimeCoordinator,
    RuntimeDependencyManager,
    RuntimeLoader,
    RuntimeRegistry,
    RuntimeSupervisor,
    GlobalScheduler,
    SystemStateManager,
)


def test_kernel_runtime_integration_smoke() -> None:
    kernel = KernelManager()
    runtime = KernelRuntime(runtime_id="planner", name="planning")
    kernel.register_runtime(runtime)

    assert kernel.get_runtime("planner") is runtime
    assert kernel.get_status("planner") == "registered"

    kernel.start()
    assert kernel.get_status("planner") == "running"

    kernel.pause()
    assert kernel.get_status("planner") == "paused"

    kernel.resume()
    assert kernel.get_status("planner") == "running"

    kernel.stop()
    assert kernel.get_status("planner") == "stopped"

    bootstrap = KernelBootstrap()
    bootstrap.initialize()
    assert bootstrap.steps()[0] == "config"

    supervisor = RuntimeSupervisor()
    supervisor.register_runtime(runtime)
    assert supervisor.get_runtime("planner") is runtime
    assert supervisor.start_runtime("planner") == "running"
    assert supervisor.restart_runtime("planner") == "running"
    assert supervisor.shutdown_runtime("planner") == "stopped"

    registry = RuntimeRegistry()
    registry.register(runtime)
    assert registry.get("planner") is runtime

    loader = RuntimeLoader()
    loaded = loader.load_runtime(runtime)
    assert loaded.status == "loaded"
    coordinator = RuntimeCoordinator()
    assert coordinator.coordinate(runtime).startswith("coordinated")

    dependency_manager = RuntimeDependencyManager()
    dependency_manager.add_dependency("planner", "memory")
    assert dependency_manager.get_dependencies("planner") == ["memory"]
    assert dependency_manager.resolve_startup_order(["planner", "memory"]) == ["memory", "planner"]

    scheduler = GlobalScheduler()
    scheduler.schedule("planner", "task", priority=3)
    assert scheduler.peek("planner") == "task"
    assert scheduler.cancel("planner", "task") is True

    resource_manager = ResourceManager()
    resource_manager.allocate("planner", "memory", 4)
    assert resource_manager.get_usage("planner", "memory") == 4
    resource_manager.release("planner", "memory")
    assert resource_manager.get_usage("planner", "memory") == 0

    state_manager = SystemStateManager()
    state_manager.set_state("kernel", {"phase": "ready"})
    assert state_manager.get_state("kernel")["phase"] == "ready"
    snapshot = state_manager.snapshot_state("kernel")
    assert snapshot.snapshot_id.startswith("snapshot")
    state_manager.restore_snapshot(snapshot.snapshot_id)

    context = KernelContext(context_id="ctx-1", profile_name="default")
    config = KernelConfiguration(configuration_id="cfg-1", profile_name="default")
    metadata = KernelMetadata(metadata_id="meta-1", name="kernel")
    health = KernelHealth(health_id="health-1", status="healthy")
    stats = KernelStatistics(statistics_id="stats-1", counters={"runtime_count": 1})

    assert context.context_id == "ctx-1"
    assert config.profile_name == "default"
    assert metadata.name == "kernel"
    assert health.status == "healthy"
    assert stats.counters["runtime_count"] == 1
