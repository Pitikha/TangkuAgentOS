from __future__ import annotations

from tangku_agentos.kernel_runtime import KernelManager


def test_kernel_bootstrap_registers_and_discovers_runtimes() -> None:
    kernel = KernelManager()
    kernel.initialize()

    assert kernel.get_runtime("memory") is not None
    assert kernel.get_runtime("planning") is not None
    assert kernel.get_runtime("reasoning") is not None
    assert "memory" in kernel.dependencies()
    assert "planning" in kernel.dependencies()


def test_kernel_startup_shutdown_restart_and_diagnostics() -> None:
    kernel = KernelManager()
    kernel.startup()

    assert kernel.status()["state"] == "running"
    assert kernel.health()["status"] in {"healthy", "degraded"}
    assert kernel.statistics()["runtime_count"] >= 1
    assert kernel.dump_state()["kernel_id"]

    kernel.shutdown()
    assert kernel.status()["state"] == "stopped"

    kernel.restart()
    assert kernel.status()["state"] == "running"


def test_kernel_routes_events_and_recovers_runtime_failures() -> None:
    kernel = KernelManager()
    kernel.startup()

    record = kernel.route_event("planning.started", {"source": "test"})
    assert record.name == "planning.started"

    recovery = kernel.recover()
    assert isinstance(recovery, list)
    assert any(item.get("action") == "recovery" for item in recovery)
