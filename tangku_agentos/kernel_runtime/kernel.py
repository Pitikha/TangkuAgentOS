from __future__ import annotations

import json
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from tangku_agentos.automation_runtime.runtime import AutomationManager
from tangku_agentos.context_engine.manager import ContextManager
from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.knowledge_engine.manager import KnowledgeManager
from tangku_agentos.memory_engine import MemoryManager
from tangku_agentos.model_runtime.manager import ModelRuntimeManager
from tangku_agentos.observability.manager import ObservabilityManager
from tangku_agentos.planning_runtime.manager import PlanningManager
from tangku_agentos.provider_runtime.manager import ProviderManager
from tangku_agentos.reasoning_runtime.manager import ReasoningManager
from tangku_agentos.repository_intelligence.manager import RepositoryManager
from tangku_agentos.security_engine.manager import SecurityManager
from tangku_agentos.terminal_runtime.manager import TerminalManager
from tangku_agentos.workflow_engine.manager import WorkflowManager
from tangku_agentos.workspace_engine.manager import WorkspaceManager


@dataclass(frozen=True)
class KernelRuntime:
    runtime_id: str
    name: str
    status: str = "registered"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelContext:
    context_id: str
    profile_name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class KernelConfiguration:
    configuration_id: str
    profile_name: str = "default"
    values: Dict[str, Any] = field(default_factory=dict)
    bootstrap_steps: tuple[str, ...] = ("config", "runtime-registration", "dependency-resolution", "health-check")


@dataclass(frozen=True)
class KernelMetadata:
    metadata_id: str
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"


@dataclass(frozen=True)
class KernelStatistics:
    statistics_id: str
    counters: Dict[str, int] = field(default_factory=dict)
    totals: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelHealth:
    health_id: str
    status: str = "healthy"
    summary: str = "healthy"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemSnapshot:
    snapshot_id: str
    state_id: str
    values: Dict[str, Any] = field(default_factory=dict)


class KernelLifecycle:
    def __init__(self) -> None:
        self._state = "stopped"
        self._lock = RLock()

    def start(self) -> None:
        with self._lock:
            self._state = "running"

    def stop(self) -> None:
        with self._lock:
            self._state = "stopped"

    def pause(self) -> None:
        with self._lock:
            self._state = "paused"

    def resume(self) -> None:
        with self._lock:
            self._state = "running"

    def state(self) -> str:
        with self._lock:
            return self._state


class KernelBootstrap:
    def __init__(self) -> None:
        self._steps: List[str] = []

    def initialize(self) -> None:
        self._steps = ["config", "runtime-registration", "dependency-resolution", "health-check", "ready"]

    def steps(self) -> List[str]:
        return list(self._steps)


class KernelManager:
    def __init__(self, config: Dict[str, Any] | None = None, event_bus: EventBus | None = None, security_manager: Any | None = None, observability_manager: Any | None = None) -> None:
        self._kernel_id = f"kernel-{uuid4().hex[:8]}"
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._runtime_instances: Dict[str, Any] = {}
        self._runtime_metadata: Dict[str, Dict[str, Any]] = {}
        self._runtime_dependencies: Dict[str, List[str]] = {}
        self._runtime_states: Dict[str, str] = {}
        self._runtime_errors: Dict[str, str] = {}
        self._services: Dict[str, Any] = {}
        self._service_scopes: Dict[str, str] = {}
        self._service_factories: Dict[str, Any] = {}
        self._config: Dict[str, Any] = dict(config or {})
        self._config_sources: Dict[str, str] = {}
        self._initialization_order: List[str] = []
        self._lock = RLock()
        self.lifecycle = KernelLifecycle()
        self.bootstrap = KernelBootstrap()
        self.supervisor = RuntimeSupervisor()
        self.registry = RuntimeRegistry()
        self.loader = RuntimeLoader()
        self.coordinator = RuntimeCoordinator()
        self.dependency_manager = RuntimeDependencyManager()
        self.scheduler = GlobalScheduler()
        self.resources = ResourceManager()
        self.state_manager = SystemStateManager()
        self.runtime_states = RuntimeStateRegistry()
        self.snapshots = SystemSnapshotManager()
        self.recovery = RecoveryManager()
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager or SecurityManager()
        self._observability_manager = observability_manager or ObservabilityManager(
            logging_manager=type("LoggingManager", (), {"snapshot": lambda self: []})(),
            metrics_manager=type("MetricsManager", (), {"snapshot": lambda self: {}})(),
            trace_manager=type("TraceManager", (), {"snapshot": lambda self: []})(),
            health_manager=type("HealthManager", (), {"snapshot": lambda self: {}})(),
            monitoring_manager=type("MonitoringManager", (), {})(),
            analytics_manager=type("AnalyticsManager", (), {})(),
            timeline_manager=type("TimelineManager", (), {})(),
            diagnostics_manager=type("DiagnosticsManager", (), {})(),
            event_recorder=type("EventRecorder", (), {"record": lambda self, *args, **kwargs: None})(),
        )
        self._memory_manager = MemoryManager()
        self._setup_builtin_runtime_definitions()
        self._register_internal_services()

    def register_runtime(self, runtime: KernelRuntime | Any, runtime_id: str | None = None, dependencies: List[str] | None = None, metadata: Dict[str, Any] | None = None) -> KernelRuntime:
        with self._lock:
            if isinstance(runtime, KernelRuntime):
                entry = runtime
                runtime_name = entry.name
                runtime_key = entry.runtime_id
            else:
                runtime_name = getattr(runtime, "name", runtime.__class__.__name__)
                runtime_key = runtime_id or getattr(runtime, "runtime_id", runtime_name)
                entry = KernelRuntime(runtime_id=runtime_key, name=runtime_name, status="registered", metadata=metadata or {})
            self._runtimes[runtime_key] = entry
            self._runtime_metadata[runtime_key] = {
                **(entry.metadata or {}),
                **(metadata or {}),
                "name": runtime_name,
                "dependencies": list(dependencies or []),
            }
            self._runtime_dependencies[runtime_key] = list(dependencies or [])
            self._runtime_states[runtime_key] = "registered"
            self.supervisor.register_runtime(entry)
            self.registry.register(entry)
            if runtime_key not in self._initialization_order:
                self._initialization_order.append(runtime_key)
            return entry

    def unregister_runtime(self, runtime_id: str) -> None:
        with self._lock:
            self._runtimes.pop(runtime_id, None)
            self._runtime_instances.pop(runtime_id, None)
            self._runtime_metadata.pop(runtime_id, None)
            self._runtime_dependencies.pop(runtime_id, None)
            self._runtime_states.pop(runtime_id, None)
            self._runtime_errors.pop(runtime_id, None)
            self.supervisor.unregister_runtime(runtime_id)
            self.registry.unregister(runtime_id)
            self._initialization_order = [item for item in self._initialization_order if item != runtime_id]

    def get_runtime(self, runtime_id: str) -> KernelRuntime | None:
        with self._lock:
            return self._runtimes.get(runtime_id)

    def lookup(self, runtime_id: str) -> KernelRuntime | None:
        return self.get_runtime(runtime_id)

    def get_status(self, runtime_id: str) -> str:
        runtime = self.get_runtime(runtime_id)
        if runtime is None:
            return "unknown"
        return runtime.status

    def get_health(self) -> str:
        return self.health()["status"]

    def get_metrics(self) -> Dict[str, Any]:
        return self.statistics()

    def initialize(self) -> Dict[str, Any]:
        self._load_configuration()
        self._register_default_runtimes()
        self.bootstrap.initialize()
        self._validate_startup()
        self._event_bus.publish("kernel.initialized", {"kernel_id": self._kernel_id})
        self._record_observability("kernel.initialized", {"kernel_id": self._kernel_id})
        self.lifecycle.resume()
        return self.dump_state()

    def startup(self) -> Dict[str, Any]:
        if not self._runtimes:
            self.initialize()
        runtime_ids = list(set(self._runtime_definitions.keys()) | set(self._runtimes.keys()))
        self._initialization_order = self.dependency_manager.resolve_startup_order(runtime_ids)
        self.lifecycle.start()
        self._event_bus.publish("kernel.startup", {"kernel_id": self._kernel_id})
        self._record_observability("kernel.startup", {"kernel_id": self._kernel_id})
        order = [runtime_id for runtime_id in self._initialization_order if runtime_id in self._runtimes or runtime_id in self._runtime_definitions]
        runtime_groups: List[List[str]] = []
        for runtime_id in order:
            if runtime_id in runtime_groups[-1] if runtime_groups else False:
                continue
            runtime_groups.append([runtime_id])
        with ThreadPoolExecutor(max_workers=max(1, min(4, len(order)))) as executor:
            futures = [executor.submit(self._start_runtime, runtime_id) for runtime_id in order]
            for future in futures:
                future.result()
        self._persist_state("startup")
        return self.status()

    def shutdown(self) -> Dict[str, Any]:
        for runtime_id in reversed(self._initialization_order):
            self._stop_runtime(runtime_id)
        self.lifecycle.stop()
        self._persist_state("shutdown")
        self._event_bus.publish("kernel.shutdown", {"kernel_id": self._kernel_id})
        self._record_observability("kernel.shutdown", {"kernel_id": self._kernel_id})
        return self.status()

    def restart(self) -> Dict[str, Any]:
        self.shutdown()
        return self.startup()

    def pause(self) -> Dict[str, Any]:
        self.lifecycle.pause()
        self._apply_runtime_status("paused")
        return self.status()

    def resume(self) -> Dict[str, Any]:
        self.lifecycle.resume()
        self._apply_runtime_status("running")
        return self.status()

    def stop(self) -> Dict[str, Any]:
        return self.shutdown()

    def start(self) -> Dict[str, Any]:
        return self.startup()

    def _apply_runtime_status(self, status: str) -> None:
        with self._lock:
            updated: Dict[str, KernelRuntime] = {}
            for runtime_id, runtime in self._runtimes.items():
                updated[runtime_id] = KernelRuntime(
                    runtime_id=runtime.runtime_id,
                    name=runtime.name,
                    status=status,
                    metadata=runtime.metadata,
                )
                self.supervisor.register_runtime(updated[runtime_id])
                self.registry.register(updated[runtime_id])
            self._runtimes = updated

    def status(self) -> Dict[str, Any]:
        return {
            "kernel_id": self._kernel_id,
            "state": self.lifecycle.state(),
            "runtimes": {
                runtime_id: {
                    "status": runtime.status,
                    "state": self._runtime_states.get(runtime_id, runtime.status),
                    "dependencies": self._runtime_dependencies.get(runtime_id, []),
                }
                for runtime_id, runtime in self._runtimes.items()
            },
            "runtime_count": len(self._runtimes),
        }

    def health(self) -> Dict[str, Any]:
        if not self._runtimes:
            return {"status": "healthy", "summary": "no runtimes registered"}
        statuses = {self._runtime_states.get(runtime_id, runtime.status) for runtime_id, runtime in self._runtimes.items()}
        if "failed" in statuses:
            status = "degraded"
            summary = "one or more runtimes failed"
        elif "restarting" in statuses:
            status = "restarting"
            summary = "runtimes are restarting"
        elif "running" in statuses or self.lifecycle.state() == "running":
            status = "healthy"
            summary = "all runtimes healthy"
        else:
            status = "stopped"
            summary = "kernel is stopped"
        return {"status": status, "summary": summary, "statuses": sorted(statuses)}

    def statistics(self) -> Dict[str, Any]:
        return {
            "kernel_id": self._kernel_id,
            "runtime_count": len(self._runtimes),
            "runtime_states": dict(self._runtime_states),
            "runtime_errors": dict(self._runtime_errors),
            "lifecycle_state": self.lifecycle.state(),
            "config_sources": dict(self._config_sources),
        }

    def dependencies(self) -> Dict[str, List[str]]:
        return {runtime_id: list(dependencies) for runtime_id, dependencies in self._runtime_dependencies.items()}

    def dump_state(self) -> Dict[str, Any]:
        return {
            "kernel_id": self._kernel_id,
            "state": self.lifecycle.state(),
            "bootstrap_steps": self.bootstrap.steps(),
            "runtimes": {runtime_id: runtime.status for runtime_id, runtime in self._runtimes.items()},
            "dependencies": self.dependencies(),
            "health": self.health(),
            "config": dict(self._config),
        }

    def route_event(self, event_name: str, payload: Dict[str, Any] | None = None, metadata: Dict[str, Any] | None = None) -> Any:
        return self._event_bus.publish(event_name, payload or {}, metadata=metadata or {})

    def recover(self) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        for runtime_id, error in list(self._runtime_errors.items()):
            self._runtime_states[runtime_id] = "restarting"
            self._record_observability("kernel.recovery", {"runtime_id": runtime_id, "error": error})
            try:
                self._start_runtime(runtime_id)
                actions.append({"runtime_id": runtime_id, "action": "recovery", "status": "recovered"})
            except Exception as exc:  # pragma: no cover - defensive path
                actions.append({"runtime_id": runtime_id, "action": "recovery", "status": "failed", "error": str(exc)})
        return actions

    def unload_runtime(self, runtime_id: str) -> None:
        self.unregister_runtime(runtime_id)

    def reload_runtime(self, runtime_id: str) -> KernelRuntime | None:
        self.unload_runtime(runtime_id)
        return self.get_runtime(runtime_id)

    def register_service(self, service_name: str, service: Any, scope: str = "singleton") -> None:
        self._services[service_name] = service
        self._service_scopes[service_name] = scope

    def register_singleton(self, service_name: str, service: Any) -> None:
        self.register_service(service_name, service, scope="singleton")

    def register_scoped_service(self, service_name: str, factory: Any) -> None:
        self._service_factories[service_name] = factory
        self._service_scopes[service_name] = "scoped"

    def resolve_service(self, service_name: str) -> Any:
        if service_name in self._services:
            return self._services[service_name]
        if service_name in self._service_factories:
            factory = self._service_factories[service_name]
            value = factory() if callable(factory) else factory
            self._services[service_name] = value
            return value
        return None

    def get_service(self, service_name: str) -> Any:
        return self.resolve_service(service_name)

    def dependencies_graph(self) -> Dict[str, List[str]]:
        return self.dependencies()

    def get_runtime_metadata(self, runtime_id: str) -> Dict[str, Any]:
        return dict(self._runtime_metadata.get(runtime_id, {}))

    def list_runtimes(self) -> List[str]:
        return sorted(self._runtimes)

    def _register_internal_services(self) -> None:
        self.register_singleton("event_bus", self._event_bus)
        self.register_singleton("memory", self._memory_manager)
        self.register_singleton("security", self._security_manager)
        self.register_singleton("observability", self._observability_manager)
        self.register_singleton("configuration", self._config)

    def _setup_builtin_runtime_definitions(self) -> None:
        self._runtime_definitions = {
            "memory": {"dependencies": [], "factory": lambda: self._memory_manager, "metadata": {"kind": "service"}},
            "planning": {"dependencies": ["memory"], "factory": lambda: PlanningManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager), "metadata": {"kind": "runtime"}},
            "reasoning": {"dependencies": ["memory", "planning"], "factory": lambda: ReasoningManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager), "metadata": {"kind": "runtime"}},
            "context": {"dependencies": ["memory"], "factory": lambda: ContextManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager), "metadata": {"kind": "runtime"}},
            "knowledge": {"dependencies": ["memory"], "factory": lambda: KnowledgeManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager), "metadata": {"kind": "runtime"}},
            "provider": {"dependencies": ["memory"], "factory": lambda: ProviderManager(), "metadata": {"kind": "runtime"}},
            "model": {"dependencies": ["provider"], "factory": lambda: ModelRuntimeManager(), "metadata": {"kind": "runtime"}},
            "workflow": {"dependencies": ["memory"], "factory": lambda: WorkflowManager(), "metadata": {"kind": "runtime"}},
            "automation": {"dependencies": ["memory", "workflow"], "factory": lambda: AutomationManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager), "metadata": {"kind": "runtime"}},
            "workspace": {"dependencies": ["memory"], "factory": lambda: WorkspaceManager(security_manager=self._security_manager, observability_manager=self._observability_manager, event_bus=self._event_bus), "metadata": {"kind": "runtime"}},
            "terminal": {"dependencies": ["workspace"], "factory": lambda: TerminalManager(), "metadata": {"kind": "runtime"}},
            "repository": {"dependencies": ["workspace"], "factory": lambda: RepositoryManager(), "metadata": {"kind": "runtime"}},
            "multi_agent": {"dependencies": ["planning", "reasoning", "workflow", "automation", "context", "knowledge", "provider", "terminal", "workspace"], "factory": lambda: None, "metadata": {"kind": "runtime"}},
            "observability": {"dependencies": ["event_bus"], "factory": lambda: self._observability_manager, "metadata": {"kind": "service"}},
            "security": {"dependencies": [], "factory": lambda: self._security_manager, "metadata": {"kind": "service"}},
            "configuration": {"dependencies": [], "factory": lambda: self._config, "metadata": {"kind": "service"}},
        }

    def _register_default_runtimes(self) -> None:
        for runtime_id in self._runtime_definitions:
            if runtime_id not in self._runtimes:
                self.register_runtime(KernelRuntime(runtime_id=runtime_id, name=runtime_id, status="registered", metadata=self._runtime_definitions[runtime_id]["metadata"]), dependencies=self._runtime_definitions[runtime_id]["dependencies"], metadata=self._runtime_definitions[runtime_id]["metadata"])
            self._runtime_dependencies[runtime_id] = self._runtime_definitions[runtime_id]["dependencies"]
            self._runtime_states[runtime_id] = self._runtime_states.get(runtime_id, "registered")
            self._runtime_metadata[runtime_id] = {
                **self._runtime_metadata.get(runtime_id, {}),
                **self._runtime_definitions[runtime_id]["metadata"],
                "dependencies": self._runtime_definitions[runtime_id]["dependencies"],
            }

    def _validate_startup(self) -> None:
        errors: List[str] = []
        for runtime_id in self._runtime_definitions:
            dependencies = self._runtime_definitions[runtime_id]["dependencies"]
            for dependency in dependencies:
                if dependency not in self._runtime_definitions:
                    errors.append(f"missing dependency {dependency} for {runtime_id}")
        if errors:
            self._runtime_states["kernel"] = "degraded"
            self._runtime_errors["kernel"] = "; ".join(errors)

    def _load_configuration(self) -> None:
        values: Dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith("TANGKU_AGENTOS_"):
                values[key.lower().replace("tangku_agentos_", "")] = value
        self._config_sources["environment"] = "environment"
        self._config.update(values)
        config_paths = [Path("config.json"), Path("tangku_agentos.json"), Path("/workspaces/TangkuAgentOS/config.json")]
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with config_path.open("r", encoding="utf-8") as handle:
                        loaded = json.load(handle)
                    self._config.update(loaded)
                    self._config_sources[str(config_path)] = str(config_path)
                except Exception:
                    continue
        if self._config:
            self._config_sources["runtime_overrides"] = "runtime_overrides"
        workspace_path = os.getenv("TANGKU_AGENTOS_WORKSPACE") or "/workspaces/TangkuAgentOS"
        workspace_config = Path(workspace_path) / "workspace.json"
        if workspace_config.exists():
            try:
                with workspace_config.open("r", encoding="utf-8") as handle:
                    workspace_values = json.load(handle)
                self._config.update(workspace_values)
                self._config_sources[str(workspace_config)] = str(workspace_config)
            except Exception:
                pass

    def _config_value(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def _start_runtime(self, runtime_id: str) -> None:
        if runtime_id not in self._runtime_definitions:
            self._runtime_states[runtime_id] = "running"
            self._runtime_errors.pop(runtime_id, None)
            runtime = self.get_runtime(runtime_id)
            runtime_name = runtime.name if runtime is not None else runtime_id
            self._runtimes[runtime_id] = KernelRuntime(runtime_id=runtime_id, name=runtime_name, status="running", metadata=self._runtime_metadata.get(runtime_id, {}))
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            return
        self._runtime_states[runtime_id] = "starting"
        try:
            runtime = self._resolve_runtime_instance(runtime_id)
            if runtime is not None and hasattr(runtime, "initialize"):
                runtime.initialize()
            if runtime is not None and hasattr(runtime, "startup"):
                runtime.startup()
            elif runtime is not None and hasattr(runtime, "start"):
                runtime.start()
            self._runtime_states[runtime_id] = "running"
            self._runtime_errors.pop(runtime_id, None)
            self._runtimes[runtime_id] = KernelRuntime(runtime_id=runtime_id, name=runtime_id, status="running", metadata=self._runtime_metadata.get(runtime_id, {}))
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
        except Exception as exc:  # pragma: no cover - defensive path
            self._runtime_states[runtime_id] = "failed"
            self._runtime_errors[runtime_id] = str(exc)
            self._runtimes[runtime_id] = KernelRuntime(runtime_id=runtime_id, name=runtime_id, status="failed", metadata=self._runtime_metadata.get(runtime_id, {}))
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            raise

    def _stop_runtime(self, runtime_id: str) -> None:
        if runtime_id not in self._runtime_definitions:
            self._runtime_states[runtime_id] = "stopped"
            runtime = self.get_runtime(runtime_id)
            runtime_name = runtime.name if runtime is not None else runtime_id
            self._runtimes[runtime_id] = KernelRuntime(runtime_id=runtime_id, name=runtime_name, status="stopped", metadata=self._runtime_metadata.get(runtime_id, {}))
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            return
        runtime = self._runtime_instances.get(runtime_id)
        if runtime is None:
            self._runtime_states[runtime_id] = "stopped"
            return
        try:
            if hasattr(runtime, "shutdown"):
                runtime.shutdown()
            elif hasattr(runtime, "stop"):
                runtime.stop()
        except Exception:  # pragma: no cover - defensive path
            pass
        self._runtime_states[runtime_id] = "stopped"
        self._runtimes[runtime_id] = KernelRuntime(runtime_id=runtime_id, name=runtime_id, status="stopped", metadata=self._runtime_metadata.get(runtime_id, {}))
        self.supervisor.register_runtime(self._runtimes[runtime_id])
        self.registry.register(self._runtimes[runtime_id])

    def _resolve_runtime_instance(self, runtime_id: str) -> Any:
        instance = self._runtime_instances.get(runtime_id)
        if instance is not None:
            return instance
        definition = self._runtime_definitions.get(runtime_id)
        if definition is None:
            return None
        factory = definition.get("factory")
        if factory is None:
            return None
        value = factory()
        if runtime_id == "multi_agent":
            if value is None:
                from tangku_agentos.coordination.runtime import MultiAgentManager
                value = MultiAgentManager(event_bus=self._event_bus, security_manager=self._security_manager, observability_manager=self._observability_manager)
        self._runtime_instances[runtime_id] = value
        self._runtime_states[runtime_id] = self._runtime_states.get(runtime_id, "registered")
        return value

    def _persist_state(self, phase: str) -> None:
        self.state_manager.set_state("kernel", {"phase": phase, "kernel_id": self._kernel_id, "config": dict(self._config)})
        self.snapshots.create_snapshot(f"snapshot-{phase}", {"phase": phase, "kernel_id": self._kernel_id})

    def _record_observability(self, event_name: str, payload: Dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload)
        except Exception:  # pragma: no cover - defensive path
            pass
        try:
            if self._observability_manager is not None and hasattr(self._observability_manager, "event_recorder"):
                self._observability_manager.event_recorder.record({"event": event_name, "payload": payload})
        except Exception:  # pragma: no cover - defensive path
            pass


class RuntimeSupervisor:
    def __init__(self) -> None:
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._lock = RLock()

    def register_runtime(self, runtime: KernelRuntime) -> None:
        with self._lock:
            self._runtimes[runtime.runtime_id] = runtime

    def unregister_runtime(self, runtime_id: str) -> None:
        with self._lock:
            self._runtimes.pop(runtime_id, None)

    def get_runtime(self, runtime_id: str) -> KernelRuntime | None:
        with self._lock:
            return self._runtimes.get(runtime_id)

    def start_runtime(self, runtime_id: str) -> str:
        with self._lock:
            runtime = self._runtimes.get(runtime_id)
            if runtime is None:
                return "unknown"
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime.runtime_id,
                name=runtime.name,
                status="running",
                metadata=runtime.metadata,
            )
            return self._runtimes[runtime_id].status

    def shutdown_runtime(self, runtime_id: str) -> str:
        with self._lock:
            runtime = self._runtimes.get(runtime_id)
            if runtime is None:
                return "unknown"
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime.runtime_id,
                name=runtime.name,
                status="stopped",
                metadata=runtime.metadata,
            )
            return self._runtimes[runtime_id].status

    def restart_runtime(self, runtime_id: str) -> str:
        return self.start_runtime(runtime_id)

    def monitor_runtime(self, runtime_id: str) -> str:
        with self._lock:
            runtime = self._runtimes.get(runtime_id)
            return runtime.status if runtime is not None else "unknown"


class RuntimeRegistry:
    def __init__(self) -> None:
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._lock = RLock()

    def register(self, runtime: KernelRuntime) -> None:
        with self._lock:
            self._runtimes[runtime.runtime_id] = runtime

    def unregister(self, runtime_id: str) -> None:
        with self._lock:
            self._runtimes.pop(runtime_id, None)

    def get(self, runtime_id: str) -> KernelRuntime | None:
        with self._lock:
            return self._runtimes.get(runtime_id)

    def list(self) -> List[KernelRuntime]:
        with self._lock:
            return list(self._runtimes.values())


class RuntimeLoader:
    def load_runtime(self, runtime: KernelRuntime) -> KernelRuntime:
        return KernelRuntime(
            runtime_id=runtime.runtime_id,
            name=runtime.name,
            status="loaded",
            metadata=runtime.metadata,
        )


class RuntimeCoordinator:
    def coordinate(self, runtime: KernelRuntime) -> str:
        return f"coordinated:{runtime.runtime_id}"


class RuntimeDependencyManager:
    def __init__(self) -> None:
        self._dependencies: Dict[str, List[str]] = {}
        self._lock = RLock()

    def dependencies(self) -> Dict[str, List[str]]:
        with self._lock:
            return {runtime_id: list(dependencies) for runtime_id, dependencies in self._dependencies.items()}

    def add_dependency(self, runtime_id: str, dependency: str) -> None:
        with self._lock:
            self._dependencies.setdefault(runtime_id, [])
            if dependency not in self._dependencies[runtime_id]:
                self._dependencies[runtime_id].append(dependency)

    def get_dependencies(self, runtime_id: str) -> List[str]:
        with self._lock:
            return list(self._dependencies.get(runtime_id, []))

    def resolve_startup_order(self, runtime_ids: List[str]) -> List[str]:
        nodes = set(runtime_ids)
        for runtime_id in runtime_ids:
            nodes.update(self.get_dependencies(runtime_id))

        indegree = {node: 0 for node in nodes}
        reverse: Dict[str, List[str]] = {node: [] for node in nodes}

        for runtime_id in runtime_ids:
            for dependency in self.get_dependencies(runtime_id):
                if dependency in nodes:
                    reverse[dependency].append(runtime_id)
                    indegree[runtime_id] += 1

        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        ordered: List[str] = []
        while queue:
            node = queue.popleft()
            ordered.append(node)
            for dependent in sorted(reverse[node]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)

        if len(ordered) != len(nodes):
            ordered.extend(sorted(node for node in nodes if node not in ordered))
        return ordered


class GlobalScheduler:
    def __init__(self) -> None:
        self._queue: Dict[str, List[tuple[int, str]]] = {}
        self._lock = RLock()

    def schedule(self, runtime_id: str, item: str, priority: int = 0) -> None:
        with self._lock:
            self._queue.setdefault(runtime_id, []).append((priority, item))
            self._queue[runtime_id].sort(key=lambda entry: entry[0], reverse=True)

    def peek(self, runtime_id: str) -> Optional[str]:
        with self._lock:
            queue = self._queue.get(runtime_id, [])
            return queue[0][1] if queue else None

    def cancel(self, runtime_id: str, item: str) -> bool:
        with self._lock:
            queue = self._queue.get(runtime_id, [])
            for index, entry in enumerate(queue):
                if entry[1] == item:
                    del queue[index]
                    return True
            return False


class RuntimeScheduler(GlobalScheduler):
    pass


class AgentScheduler(GlobalScheduler):
    pass


class WorkflowScheduler(GlobalScheduler):
    pass


class TaskScheduler(GlobalScheduler):
    pass


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: Dict[str, Dict[str, int]] = {}
        self._lock = RLock()

    def set(self, resource_id: str, values: Dict[str, int]) -> None:
        with self._lock:
            self._resources[resource_id] = dict(values)

    def get(self, resource_id: str) -> Dict[str, int] | None:
        with self._lock:
            return self._resources.get(resource_id)


class ResourceManager:
    def __init__(self) -> None:
        self._usages: Dict[tuple[str, str], int] = {}
        self._lock = RLock()

    def allocate(self, runtime_id: str, resource_name: str, amount: int) -> None:
        with self._lock:
            self._usages[(runtime_id, resource_name)] = amount

    def release(self, runtime_id: str, resource_name: str) -> int:
        with self._lock:
            amount = self._usages.pop((runtime_id, resource_name), 0)
            return amount

    def get_usage(self, runtime_id: str, resource_name: str) -> int:
        with self._lock:
            return self._usages.get((runtime_id, resource_name), 0)


class MemoryBudgetManager(ResourceManager):
    pass


class ComputeBudgetManager(ResourceManager):
    pass


class SessionResourceManager(ResourceManager):
    pass


class SystemStateManager:
    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, SystemSnapshot] = {}
        self._lock = RLock()

    def set_state(self, state_id: str, values: Dict[str, Any]) -> None:
        with self._lock:
            self._states[state_id] = dict(values)

    def get_state(self, state_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._states.get(state_id, {}))

    def snapshot_state(self, state_id: str) -> SystemSnapshot:
        with self._lock:
            values = dict(self._states.get(state_id, {}))
            snapshot = SystemSnapshot(snapshot_id=f"snapshot-{uuid4().hex[:8]}", state_id=state_id, values=values)
            self._snapshots[snapshot.snapshot_id] = snapshot
            return snapshot

    def restore_snapshot(self, snapshot_id: str) -> bool:
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
            if snapshot is None:
                return False
            self._states[snapshot.state_id] = dict(snapshot.values)
            return True


class RuntimeStateRegistry:
    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, runtime_id: str, values: Dict[str, Any]) -> None:
        with self._lock:
            self._states[runtime_id] = dict(values)

    def get(self, runtime_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._states.get(runtime_id, {}))


class SystemSnapshotManager:
    def __init__(self) -> None:
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def create_snapshot(self, snapshot_id: str, values: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshots[snapshot_id] = dict(values)

    def get_snapshot(self, snapshot_id: str) -> Dict[str, Any] | None:
        with self._lock:
            return self._snapshots.get(snapshot_id)


class RecoveryManager:
    def __init__(self) -> None:
        self._plans: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def plan_recovery(self, runtime_id: str, values: Dict[str, Any]) -> None:
        with self._lock:
            self._plans[runtime_id] = dict(values)

    def get_plan(self, runtime_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._plans.get(runtime_id, {}))
