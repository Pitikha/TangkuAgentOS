"""Main kernel module for TangkuAgentOS.

This module provides the `KernelManager` class, which is the central component
responsible for managing the lifecycle, configuration, and coordination of all
runtimes in the TangkuAgentOS system. It integrates with other modules to
provide a unified interface for kernel operations.

The `KernelManager` class is the primary entry point for interacting with the
kernel runtime system. It provides methods for registering and managing runtimes,
starting and stopping the kernel, and monitoring the health and status of the
system.
"""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, Final, List, Optional, Type
from uuid import uuid4

# Import from core_runtime
from tangku_agentos.core_runtime.event_bus import EventBus

# Import from kernel_runtime modules
from .bootstrap import KernelBootstrap
from .dependency_manager import RuntimeDependencyManager
from .health import KernelHealthMonitor
from .lifecycle import KernelLifecycle
from .recovery import RecoveryManager
from .resources import (
    ComputeBudgetManager,
    MemoryBudgetManager,
    ResourceManager,
    ResourceRegistry,
    SessionResourceManager,
)
from .runtime_coordinator import RuntimeCoordinator
from .runtime_loader import RuntimeLoader
from .runtime_registry import RuntimeRegistry
from .runtime_supervisor import RuntimeSupervisor
from .scheduler import (
    AgentScheduler,
    GlobalScheduler,
    RuntimeScheduler,
    TaskScheduler,
    WorkflowScheduler,
)
from .state import (
    RuntimeStateRegistry,
    SystemSnapshotManager,
    SystemStateManager,
)
from .types import (
    KernelConfiguration,
    KernelContext,
    KernelHealth,
    KernelMetadata,
    KernelRuntime,
    KernelStatistics,
    SystemSnapshot,
)

# Logger for the kernel module
_logger = logging.getLogger(__name__)


class KernelManager:
    """Central manager for the TangkuAgentOS kernel runtime system.

    This class is responsible for orchestrating the lifecycle of all runtimes,
    managing their dependencies, and providing a unified interface for kernel
    operations. It integrates with other modules to provide a complete runtime
    management system.

    Attributes:
        _kernel_id: Unique identifier for the kernel instance.
        _runtimes: Dictionary of registered runtimes.
        _runtime_instances: Dictionary of runtime instances.
        _runtime_metadata: Dictionary of runtime metadata.
        _runtime_dependencies: Dictionary of runtime dependencies.
        _runtime_states: Dictionary of runtime states.
        _runtime_errors: Dictionary of runtime errors.
        _services: Dictionary of registered services.
        _service_scopes: Dictionary of service scopes.
        _service_factories: Dictionary of service factories.
        _config: Dictionary of kernel configuration.
        _config_sources: Dictionary of configuration sources.
        _initialization_order: List of runtime IDs in initialization order.
        _lock: Reentrant lock for thread-safe operations.
        lifecycle: Kernel lifecycle manager.
        bootstrap: Kernel bootstrap manager.
        supervisor: Runtime supervisor.
        registry: Runtime registry.
        loader: Runtime loader.
        coordinator: Runtime coordinator.
        dependency_manager: Runtime dependency manager.
        scheduler: Global scheduler.
        resources: Resource manager.
        state_manager: System state manager.
        runtime_states: Runtime state registry.
        snapshots: System snapshot manager.
        recovery: Recovery manager.
        _event_bus: Event bus for kernel events.
        _security_manager: Security manager for runtime security.
        _observability_manager: Observability manager for monitoring.
        _memory_manager: Memory manager for runtime memory.
        _runtime_definitions: Dictionary of built-in runtime definitions.

    Example:
        >>> kernel = KernelManager()
        >>> kernel.initialize()
        >>> kernel.startup()
        >>> kernel.shutdown()
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        event_bus: Optional[EventBus] = None,
        security_manager: Optional[Any] = None,
        observability_manager: Optional[Any] = None,
    ) -> None:
        """Initializes the kernel manager.

        Args:
            config: Optional dictionary of kernel configuration.
            event_bus: Optional event bus for kernel events.
            security_manager: Optional security manager for runtime security.
            observability_manager: Optional observability manager for monitoring.
        """
        # Initialize kernel ID and core data structures
        self._kernel_id: Final[str] = f"kernel-{uuid4().hex[:8]}"
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._runtime_instances: Dict[str, Any] = {}
        self._runtime_metadata: Dict[str, Dict[str, Any]] = {}
        self._runtime_dependencies: Dict[str, List[str]] = {}
        self._runtime_states: Dict[str, str] = {}
        self._runtime_errors: Dict[str, str] = {}
        self._services: Dict[str, Any] = {}
        self._service_scopes: Dict[str, str] = {}
        self._service_factories: Dict[str, Callable[[], Any]] = {}
        self._config: Dict[str, Any] = dict(config or {})
        self._config_sources: Dict[str, str] = {}
        self._initialization_order: List[str] = []
        self._lock: Final[RLock] = RLock()

        # Initialize kernel components
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

        # Initialize external managers
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._memory_manager = None  # Will be initialized in _setup_builtin_runtime_definitions

        # Initialize runtime definitions and internal services
        self._runtime_definitions: Dict[str, Dict[str, Any]] = {}
        self._setup_builtin_runtime_definitions()
        self._register_internal_services()

    # -------------------------------------------------------------------------- #
    # Public API: Runtime Management
    # -------------------------------------------------------------------------- #

    def register_runtime(
        self,
        runtime: KernelRuntime | Any,
        runtime_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KernelRuntime:
        """Registers a runtime with the kernel.

        Args:
            runtime: The runtime to register. Can be a `KernelRuntime` object or any
                object with `name` and `runtime_id` attributes.
            runtime_id: Optional explicit runtime ID. If not provided, the runtime's
                `runtime_id` attribute or its class name will be used.
            dependencies: Optional list of runtime IDs that this runtime depends on.
            metadata: Optional dictionary of metadata to associate with the runtime.

        Returns:
            The registered `KernelRuntime` object.

        Raises:
            RuntimeError: If the runtime cannot be registered.
        """
        with self._lock:
            try:
                if isinstance(runtime, KernelRuntime):
                    entry = runtime
                    runtime_name = entry.name
                    runtime_key = entry.runtime_id
                else:
                    runtime_name = getattr(runtime, "name", runtime.__class__.__name__)
                    runtime_key = runtime_id or getattr(
                        runtime, "runtime_id", runtime_name
                    )
                    entry = KernelRuntime(
                        runtime_id=runtime_key,
                        name=runtime_name,
                        status="registered",
                        metadata=metadata or {},
                    )

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

                _logger.debug(
                    f"Registered runtime: {runtime_key} (name={runtime_name})"
                )
                return entry
            except Exception as e:
                _logger.error(f"Failed to register runtime: {e}")
                from .exceptions import RuntimeError
                raise RuntimeError(f"Failed to register runtime: {e}") from e

    def unregister_runtime(self, runtime_id: str) -> None:
        """Unregisters a runtime from the kernel.

        Args:
            runtime_id: The ID of the runtime to unregister.

        Raises:
            RuntimeError: If the runtime cannot be unregistered.
        """
        with self._lock:
            try:
                self._runtimes.pop(runtime_id, None)
                self._runtime_instances.pop(runtime_id, None)
                self._runtime_metadata.pop(runtime_id, None)
                self._runtime_dependencies.pop(runtime_id, None)
                self._runtime_states.pop(runtime_id, None)
                self._runtime_errors.pop(runtime_id, None)
                self.supervisor.unregister_runtime(runtime_id)
                self.registry.unregister(runtime_id)
                self._initialization_order = [
                    item for item in self._initialization_order if item != runtime_id
                ]
                _logger.debug(f"Unregistered runtime: {runtime_id}")
            except Exception as e:
                _logger.error(f"Failed to unregister runtime {runtime_id}: {e}")
                from .exceptions import RuntimeError
                raise RuntimeError(
                    f"Failed to unregister runtime {runtime_id}: {e}"
                ) from e

    def get_runtime(self, runtime_id: str) -> Optional[KernelRuntime]:
        """Retrieves a runtime by its ID.

        Args:
            runtime_id: The ID of the runtime to retrieve.

        Returns:
            The `KernelRuntime` object if found, otherwise `None`.
        """
        with self._lock:
            return self._runtimes.get(runtime_id)

    def lookup(self, runtime_id: str) -> Optional[KernelRuntime]:
        """Alias for `get_runtime`.

        Args:
            runtime_id: The ID of the runtime to retrieve.

        Returns:
            The `KernelRuntime` object if found, otherwise `None`.
        """
        return self.get_runtime(runtime_id)

    def get_status(self, runtime_id: str) -> str:
        """Retrieves the status of a runtime.

        Args:
            runtime_id: The ID of the runtime.

        Returns:
            The status of the runtime, or "unknown" if the runtime was not found.
        """
        runtime = self.get_runtime(runtime_id)
        if runtime is None:
            return "unknown"
        return runtime.status

    def get_runtime_metadata(self, runtime_id: str) -> Dict[str, Any]:
        """Retrieves metadata for a runtime.

        Args:
            runtime_id: The ID of the runtime.

        Returns:
            A dictionary of metadata associated with the runtime.
        """
        return dict(self._runtime_metadata.get(runtime_id, {}))

    def list_runtimes(self) -> List[str]:
        """Lists all registered runtime IDs.

        Returns:
            A sorted list of runtime IDs.
        """
        return sorted(self._runtimes)

    # -------------------------------------------------------------------------- #
    # Public API: Lifecycle Management
    # -------------------------------------------------------------------------- #

    def initialize(self) -> Dict[str, Any]:
        """Initializes the kernel and its runtimes.

        This method loads the kernel configuration, registers default runtimes,
        and performs validation to ensure the kernel is ready to start.

        Returns:
            A dictionary containing the kernel's state after initialization.

        Raises:
            ConfigurationError: If the kernel configuration is invalid.
            RuntimeError: If initialization fails.
        """
        try:
            self._load_configuration()
            self._register_default_runtimes()
            self.bootstrap.initialize()
            self._validate_startup()

            self._event_bus.publish(
                "kernel.initialized", {"kernel_id": self._kernel_id}
            )
            self._record_observability(
                "kernel.initialized", {"kernel_id": self._kernel_id}
            )
            self.lifecycle.resume()
            _logger.info(f"Kernel {self._kernel_id} initialized successfully")
            return self.dump_state()
        except Exception as e:
            _logger.error(f"Kernel initialization failed: {e}")
            from .exceptions import RuntimeError
            raise RuntimeError(f"Kernel initialization failed: {e}") from e

    def startup(self) -> Dict[str, Any]:
        """Starts the kernel and all registered runtimes.

        This method resolves the startup order for all runtimes based on their
        dependencies and starts them in parallel using a thread pool.

        Returns:
            A dictionary containing the kernel's status after startup.

        Raises:
            RuntimeError: If startup fails.
        """
        try:
            if not self._runtimes:
                self.initialize()

            runtime_ids = list(
                set(self._runtime_definitions.keys())
                | set(self._runtimes.keys())
            )
            self._initialization_order = (
                self.dependency_manager.resolve_startup_order(runtime_ids)
            )
            self.lifecycle.start()

            self._event_bus.publish(
                "kernel.startup", {"kernel_id": self._kernel_id}
            )
            self._record_observability(
                "kernel.startup", {"kernel_id": self._kernel_id}
            )

            order = [
                runtime_id
                for runtime_id in self._initialization_order
                if runtime_id in self._runtimes
                or runtime_id in self._runtime_definitions
            ]
            runtime_groups: List[List[str]] = []
            for runtime_id in order:
                if (
                    runtime_groups
                    and runtime_id in runtime_groups[-1]
                ):
                    continue
                runtime_groups.append([runtime_id])

            # Start runtimes in parallel
            max_workers = max(1, min(4, len(order)))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self._start_runtime, runtime_id)
                    for runtime_id in order
                ]
                for future in futures:
                    future.result()  # Re-raise exceptions if any

            self._persist_state("startup")
            _logger.info(f"Kernel {self._kernel_id} started successfully")
            return self.status()
        except Exception as e:
            _logger.error(f"Kernel startup failed: {e}")
            from .exceptions import RuntimeError
            raise RuntimeError(f"Kernel startup failed: {e}") from e

    def shutdown(self) -> Dict[str, Any]:
        """Shuts down the kernel and all registered runtimes.

        This method stops all runtimes in reverse order of their initialization
        and transitions the kernel to the "stopped" state.

        Returns:
            A dictionary containing the kernel's status after shutdown.

        Raises:
            RuntimeError: If shutdown fails.
        """
        try:
            for runtime_id in reversed(self._initialization_order):
                self._stop_runtime(runtime_id)

            self.lifecycle.stop()
            self._persist_state("shutdown")

            self._event_bus.publish(
                "kernel.shutdown", {"kernel_id": self._kernel_id}
            )
            self._record_observability(
                "kernel.shutdown", {"kernel_id": self._kernel_id}
            )
            _logger.info(f"Kernel {self._kernel_id} shut down successfully")
            return self.status()
        except Exception as e:
            _logger.error(f"Kernel shutdown failed: {e}")
            from .exceptions import RuntimeError
            raise RuntimeError(f"Kernel shutdown failed: {e}") from e

    def restart(self) -> Dict[str, Any]:
        """Restarts the kernel by shutting down and starting up again.

        Returns:
            A dictionary containing the kernel's status after restart.

        Raises:
            RuntimeError: If restart fails.
        """
        self.shutdown()
        return self.startup()

    def pause(self) -> Dict[str, Any]:
        """Pauses the kernel and all runtimes.

        Returns:
            A dictionary containing the kernel's status after pausing.
        """
        self.lifecycle.pause()
        self._apply_runtime_status("paused")
        _logger.info(f"Kernel {self._kernel_id} paused")
        return self.status()

    def resume(self) -> Dict[str, Any]:
        """Resumes the kernel and all runtimes.

        Returns:
            A dictionary containing the kernel's status after resuming.
        """
        self.lifecycle.resume()
        self._apply_runtime_status("running")
        _logger.info(f"Kernel {self._kernel_id} resumed")
        return self.status()

    def stop(self) -> Dict[str, Any]:
        """Alias for `shutdown`.

        Returns:
            A dictionary containing the kernel's status after stopping.
        """
        return self.shutdown()

    def start(self) -> Dict[str, Any]:
        """Alias for `startup`.

        Returns:
            A dictionary containing the kernel's status after starting.
        """
        return self.startup()

    # -------------------------------------------------------------------------- #
    # Public API: Health and Status
    # -------------------------------------------------------------------------- #

    def health(self) -> Dict[str, Any]:
        """Retrieves the health status of the kernel.

        Returns:
            A dictionary containing the health status, summary, and statuses.
        """
        if not self._runtimes:
            return {"status": "healthy", "summary": "no runtimes registered"}

        runtime_states = {
            self._runtime_states.get(runtime_id, runtime.status)
            for runtime_id, runtime in self._runtimes.items()
        }
        return KernelHealthMonitor.get_health(
            runtime_states, self.lifecycle.state()
        )

    def get_health(self) -> str:
        """Retrieves the health status of the kernel as a string.

        Returns:
            The health status (e.g., "healthy", "degraded").
        """
        return self.health()["status"]

    def statistics(self) -> Dict[str, Any]:
        """Retrieves statistics about the kernel and its runtimes.

        Returns:
            A dictionary containing kernel statistics.
        """
        return {
            "kernel_id": self._kernel_id,
            "runtime_count": len(self._runtimes),
            "runtime_states": dict(self._runtime_states),
            "runtime_errors": dict(self._runtime_errors),
            "lifecycle_state": self.lifecycle.state(),
            "config_sources": dict(self._config_sources),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Alias for `statistics`.

        Returns:
            A dictionary containing kernel metrics.
        """
        return self.statistics()

    def status(self) -> Dict[str, Any]:
        """Retrieves the current status of the kernel and its runtimes.

        Returns:
            A dictionary containing the kernel's status, including runtime states
            and dependencies.
        """
        return {
            "kernel_id": self._kernel_id,
            "state": self.lifecycle.state(),
            "runtimes": {
                runtime_id: {
                    "status": runtime.status,
                    "state": self._runtime_states.get(runtime_id, runtime.status),
                    "dependencies": self._runtime_dependencies.get(
                        runtime_id, []
                    ),
                }
                for runtime_id, runtime in self._runtimes.items()
            },
            "runtime_count": len(self._runtimes),
        }

    def dump_state(self) -> Dict[str, Any]:
        """Dumps the current state of the kernel.

        Returns:
            A dictionary containing the kernel's state, including bootstrap steps,
            runtimes, dependencies, health, and configuration.
        """
        return {
            "kernel_id": self._kernel_id,
            "state": self.lifecycle.state(),
            "bootstrap_steps": self.bootstrap.steps(),
            "runtimes": {
                runtime_id: runtime.status
                for runtime_id, runtime in self._runtimes.items()
            },
            "dependencies": self.dependencies(),
            "health": self.health(),
            "config": dict(self._config),
        }

    def dependencies(self) -> Dict[str, List[str]]:
        """Retrieves the dependency graph for all runtimes.

        Returns:
            A dictionary mapping runtime IDs to their dependency lists.
        """
        return {
            runtime_id: list(dependencies)
            for runtime_id, dependencies in self._runtime_dependencies.items()
        }

    def dependencies_graph(self) -> Dict[str, List[str]]:
        """Alias for `dependencies`.

        Returns:
            A dictionary mapping runtime IDs to their dependency lists.
        """
        return self.dependencies()

    # -------------------------------------------------------------------------- #
    # Public API: Event and Service Management
    # -------------------------------------------------------------------------- #

    def route_event(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Routes an event through the kernel's event bus.

        Args:
            event_name: The name of the event to publish.
            payload: Optional payload to include with the event.
            metadata: Optional metadata to include with the event.

        Returns:
            The event record created by the event bus.
        """
        return self._event_bus.publish(
            event_name, payload or {}, metadata=metadata or {}
        )

    def register_service(
        self, service_name: str, service: Any, scope: str = "singleton"
    ) -> None:
        """Registers a service with the kernel.

        Args:
            service_name: The name of the service to register.
            service: The service instance to register.
            scope: The scope of the service (e.g., "singleton", "scoped").
        """
        self._services[service_name] = service
        self._service_scopes[service_name] = scope
        _logger.debug(f"Registered service: {service_name} (scope={scope})")

    def register_singleton(self, service_name: str, service: Any) -> None:
        """Registers a singleton service with the kernel.

        Args:
            service_name: The name of the service to register.
            service: The service instance to register.
        """
        self.register_service(service_name, service, scope="singleton")

    def register_scoped_service(
        self, service_name: str, factory: Callable[[], Any]
    ) -> None:
        """Registers a scoped service factory with the kernel.

        Args:
            service_name: The name of the service to register.
            factory: A callable that creates the service instance.
        """
        self._service_factories[service_name] = factory
        self._service_scopes[service_name] = "scoped"
        _logger.debug(f"Registered scoped service factory: {service_name}")

    def resolve_service(self, service_name: str) -> Any:
        """Resolves a service by its name.

        Args:
            service_name: The name of the service to resolve.

        Returns:
            The service instance if found, otherwise `None`.
        """
        if service_name in self._services:
            return self._services[service_name]

        if service_name in self._service_factories:
            factory = self._service_factories[service_name]
            value = factory() if callable(factory) else factory
            self._services[service_name] = value
            return value

        return None

    def get_service(self, service_name: str) -> Any:
        """Alias for `resolve_service`.

        Args:
            service_name: The name of the service to retrieve.

        Returns:
            The service instance if found, otherwise `None`.
        """
        return self.resolve_service(service_name)

    # -------------------------------------------------------------------------- #
    # Public API: Recovery
    # -------------------------------------------------------------------------- #

    def recover(self) -> List[Dict[str, Any]]:
        """Recovers failed runtimes by restarting them.

        Returns:
            A list of dictionaries representing the recovery actions taken.
        """
        actions: List[Dict[str, Any]] = []
        for runtime_id, error in list(self._runtime_errors.items()):
            self._runtime_states[runtime_id] = "restarting"
            self._record_observability(
                "kernel.recovery", {"runtime_id": runtime_id, "error": error}
            )
            try:
                self._start_runtime(runtime_id)
                actions.append(
                    {
                        "runtime_id": runtime_id,
                        "action": "recovery",
                        "status": "recovered",
                    }
                )
                self.recovery.record_recovery_action(
                    runtime_id, "recovery", "recovered"
                )
            except Exception as exc:
                actions.append(
                    {
                        "runtime_id": runtime_id,
                        "action": "recovery",
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                self.recovery.record_recovery_action(
                    runtime_id, "recovery", "failed", str(exc)
                )
        return actions

    def unload_runtime(self, runtime_id: str) -> None:
        """Unloads a runtime from the kernel.

        Args:
            runtime_id: The ID of the runtime to unload.
        """
        self.unregister_runtime(runtime_id)

    def reload_runtime(self, runtime_id: str) -> Optional[KernelRuntime]:
        """Reloads a runtime by unloading and reloading it.

        Args:
            runtime_id: The ID of the runtime to reload.

        Returns:
            The reloaded `KernelRuntime` object, or `None` if the runtime was not found.
        """
        self.unload_runtime(runtime_id)
        return self.get_runtime(runtime_id)

    # -------------------------------------------------------------------------- #
    # Internal Methods: Runtime Management
    # -------------------------------------------------------------------------- #

    def _apply_runtime_status(self, status: str) -> None:
        """Applies a status to all runtimes.

        Args:
            status: The status to apply (e.g., "paused", "running").
        """
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
            self._runtimes.update(updated)

    def _start_runtime(self, runtime_id: str) -> None:
        """Starts a runtime and updates its state.

        Args:
            runtime_id: The ID of the runtime to start.

        Raises:
            RuntimeResolutionError: If the runtime cannot be resolved.
            RuntimeError: If the runtime cannot be started.
        """
        if runtime_id not in self._runtime_definitions:
            self._runtime_states[runtime_id] = "running"
            self._runtime_errors.pop(runtime_id, None)
            runtime = self.get_runtime(runtime_id)
            runtime_name = runtime.name if runtime is not None else runtime_id
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime_id,
                name=runtime_name,
                status="running",
                metadata=self._runtime_metadata.get(runtime_id, {}),
            )
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            _logger.debug(f"Started runtime: {runtime_id}")
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
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime_id,
                name=runtime_id,
                status="running",
                metadata=self._runtime_metadata.get(runtime_id, {}),
            )
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            _logger.debug(f"Started runtime: {runtime_id}")
        except Exception as exc:
            self._runtime_states[runtime_id] = "failed"
            self._runtime_errors[runtime_id] = str(exc)
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime_id,
                name=runtime_id,
                status="failed",
                metadata=self._runtime_metadata.get(runtime_id, {}),
            )
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            _logger.error(f"Failed to start runtime {runtime_id}: {exc}")
            from .exceptions import RuntimeError
            raise RuntimeError(f"Failed to start runtime {runtime_id}: {exc}") from exc

    def _stop_runtime(self, runtime_id: str) -> None:
        """Stops a runtime and updates its state.

        Args:
            runtime_id: The ID of the runtime to stop.
        """
        if runtime_id not in self._runtime_definitions:
            self._runtime_states[runtime_id] = "stopped"
            runtime = self.get_runtime(runtime_id)
            runtime_name = runtime.name if runtime is not None else runtime_id
            self._runtimes[runtime_id] = KernelRuntime(
                runtime_id=runtime_id,
                name=runtime_name,
                status="stopped",
                metadata=self._runtime_metadata.get(runtime_id, {}),
            )
            self.supervisor.register_runtime(self._runtimes[runtime_id])
            self.registry.register(self._runtimes[runtime_id])
            _logger.debug(f"Stopped runtime: {runtime_id}")
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
        except Exception as e:
            _logger.error(f"Error stopping runtime {runtime_id}: {e}")

        self._runtime_states[runtime_id] = "stopped"
        self._runtimes[runtime_id] = KernelRuntime(
            runtime_id=runtime_id,
            name=runtime_id,
            status="stopped",
            metadata=self._runtime_metadata.get(runtime_id, {}),
        )
        self.supervisor.register_runtime(self._runtimes[runtime_id])
        self.registry.register(self._runtimes[runtime_id])
        _logger.debug(f"Stopped runtime: {runtime_id}")

    def _resolve_runtime_instance(self, runtime_id: str) -> Any:
        """Resolves a runtime instance from its definition.

        Args:
            runtime_id: The ID of the runtime to resolve.

        Returns:
            The resolved runtime instance, or `None` if the runtime cannot be resolved.

        Raises:
            RuntimeResolutionError: If the runtime cannot be resolved.
        """
        instance = self._runtime_instances.get(runtime_id)
        if instance is not None:
            return instance

        definition = self._runtime_definitions.get(runtime_id)
        if definition is None:
            return None

        factory = definition.get("factory")
        if factory is None:
            return None

        try:
            value = factory()
            if runtime_id == "multi_agent":
                if value is None:
                    from tangku_agentos.coordination.runtime import MultiAgentManager

                    value = MultiAgentManager(
                        event_bus=self._event_bus,
                        security_manager=self._security_manager,
                        observability_manager=self._observability_manager,
                    )
            self._runtime_instances[runtime_id] = value
            self._runtime_states[runtime_id] = self._runtime_states.get(
                runtime_id, "registered"
            )
            _logger.debug(f"Resolved runtime instance: {runtime_id}")
            return value
        except Exception as e:
            _logger.error(f"Failed to resolve runtime {runtime_id}: {e}")
            from .exceptions import RuntimeResolutionError
            raise RuntimeResolutionError(
                f"Failed to resolve runtime {runtime_id}: {e}"
            ) from e

    # -------------------------------------------------------------------------- #
    # Internal Methods: Configuration and Setup
    # -------------------------------------------------------------------------- #

    def _setup_builtin_runtime_definitions(self) -> None:
        """Sets up the definitions for built-in runtimes.

        This method initializes the `_runtime_definitions` dictionary with
        definitions for all built-in runtimes, including their dependencies,
        factories, and metadata.
        """
        # Import managers lazily to avoid circular imports
        from tangku_agentos.automation_runtime.runtime import AutomationManager
        from tangku_agentos.context_engine.manager import ContextManager
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

        # Initialize memory manager if not already set
        if self._memory_manager is None:
            self._memory_manager = MemoryManager()

        # Initialize observability manager if not provided
        if self._observability_manager is None:
            self._observability_manager = ObservabilityManager(
                logging_manager=type(
                    "LoggingManager", (), {"snapshot": lambda self: []}
                )(),
                metrics_manager=type(
                    "MetricsManager", (), {"snapshot": lambda self: {}}
                )(),
                trace_manager=type(
                    "TraceManager", (), {"snapshot": lambda self: []}
                )(),
                health_manager=type(
                    "HealthManager", (), {"snapshot": lambda self: {}}
                )(),
                monitoring_manager=type("MonitoringManager", (), {})(),
                analytics_manager=type("AnalyticsManager", (), {})(),
                timeline_manager=type("TimelineManager", (), {})(),
                diagnostics_manager=type("DiagnosticsManager", (), {})(),
                event_recorder=type(
                    "EventRecorder", (), {"record": lambda self, *args, **kwargs: None}
                )(),
            )

        # Initialize security manager if not provided
        if self._security_manager is None:
            self._security_manager = SecurityManager()

        # Define built-in runtimes
        self._runtime_definitions = {
            "memory": {
                "dependencies": [],
                "factory": lambda: self._memory_manager,
                "metadata": {"kind": "service"},
            },
            "planning": {
                "dependencies": ["memory"],
                "factory": lambda: PlanningManager(
                    event_bus=self._event_bus,
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                ),
                "metadata": {"kind": "runtime"},
            },
            "reasoning": {
                "dependencies": ["memory", "planning"],
                "factory": lambda: ReasoningManager(
                    event_bus=self._event_bus,
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                ),
                "metadata": {"kind": "runtime"},
            },
            "context": {
                "dependencies": ["memory"],
                "factory": lambda: ContextManager(
                    event_bus=self._event_bus,
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                ),
                "metadata": {"kind": "runtime"},
            },
            "knowledge": {
                "dependencies": ["memory"],
                "factory": lambda: KnowledgeManager(
                    event_bus=self._event_bus,
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                ),
                "metadata": {"kind": "runtime"},
            },
            "provider": {
                "dependencies": ["memory"],
                "factory": lambda: ProviderManager(),
                "metadata": {"kind": "runtime"},
            },
            "model": {
                "dependencies": ["provider"],
                "factory": lambda: ModelRuntimeManager(),
                "metadata": {"kind": "runtime"},
            },
            "workflow": {
                "dependencies": ["memory"],
                "factory": lambda: WorkflowManager(),
                "metadata": {"kind": "runtime"},
            },
            "automation": {
                "dependencies": ["memory", "workflow"],
                "factory": lambda: AutomationManager(
                    event_bus=self._event_bus,
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                ),
                "metadata": {"kind": "runtime"},
            },
            "workspace": {
                "dependencies": ["memory"],
                "factory": lambda: WorkspaceManager(
                    security_manager=self._security_manager,
                    observability_manager=self._observability_manager,
                    event_bus=self._event_bus,
                ),
                "metadata": {"kind": "runtime"},
            },
            "terminal": {
                "dependencies": ["workspace"],
                "factory": lambda: TerminalManager(),
                "metadata": {"kind": "runtime"},
            },
            "repository": {
                "dependencies": ["workspace"],
                "factory": lambda: RepositoryManager(),
                "metadata": {"kind": "runtime"},
            },
            "multi_agent": {
                "dependencies": [
                    "planning",
                    "reasoning",
                    "workflow",
                    "automation",
                    "context",
                    "knowledge",
                    "provider",
                    "terminal",
                    "workspace",
                ],
                "factory": lambda: None,
                "metadata": {"kind": "runtime"},
            },
            "observability": {
                "dependencies": ["event_bus"],
                "factory": lambda: self._observability_manager,
                "metadata": {"kind": "service"},
            },
            "security": {
                "dependencies": [],
                "factory": lambda: self._security_manager,
                "metadata": {"kind": "service"},
            },
            "configuration": {
                "dependencies": [],
                "factory": lambda: self._config,
                "metadata": {"kind": "service"},
            },
        }

    def _register_default_runtimes(self) -> None:
        """Registers the default runtimes defined in `_runtime_definitions`.

        This method iterates over all runtime definitions and registers them
        with the kernel if they have not already been registered.
        """
        for runtime_id in self._runtime_definitions:
            if runtime_id not in self._runtimes:
                self.register_runtime(
                    KernelRuntime(
                        runtime_id=runtime_id,
                        name=runtime_id,
                        status="registered",
                        metadata=self._runtime_definitions[runtime_id]["metadata"],
                    ),
                    dependencies=self._runtime_definitions[runtime_id][
                        "dependencies"
                    ],
                    metadata=self._runtime_definitions[runtime_id]["metadata"],
                )
            self._runtime_dependencies[runtime_id] = (
                self._runtime_definitions[runtime_id]["dependencies"]
            )
            self._runtime_states[runtime_id] = self._runtime_states.get(
                runtime_id, "registered"
            )
            self._runtime_metadata[runtime_id] = {
                **self._runtime_metadata.get(runtime_id, {}),
                **self._runtime_definitions[runtime_id]["metadata"],
                "dependencies": self._runtime_definitions[runtime_id]["dependencies"],
            }

    def _validate_startup(self) -> None:
        """Validates the startup configuration of the kernel.

        This method checks that all runtime dependencies are defined and
        updates the kernel state if validation fails.
        """
        errors: List[str] = []
        for runtime_id in self._runtime_definitions:
            dependencies = self._runtime_definitions[runtime_id]["dependencies"]
            for dependency in dependencies:
                if dependency not in self._runtime_definitions:
                    errors.append(
                        f"Missing dependency {dependency} for {runtime_id}"
                    )

        if errors:
            self._runtime_states["kernel"] = "degraded"
            self._runtime_errors["kernel"] = "; ".join(errors)
            _logger.error(f"Startup validation failed: {errors}")

    def _load_configuration(self) -> None:
        """Loads the kernel configuration from environment variables and files.

        This method loads configuration from:
        1. Environment variables prefixed with `TANGKU_AGENTOS_`.
        2. Configuration files (`config.json`, `tangku_agentos.json`).
        3. Workspace configuration (`workspace.json`).
        """
        values: Dict[str, Any] = {}

        # Load from environment variables
        for key, value in os.environ.items():
            if key.startswith("TANGKU_AGENTOS_"):
                normalized_key = key.lower().replace("tangku_agentos_", "")
                values[normalized_key] = value
        self._config_sources["environment"] = "environment"
        self._config.update(values)

        # Load from configuration files
        config_paths = [
            Path("config.json"),
            Path("tangku_agentos.json"),
            Path("/workspaces/TangkuAgentOS/config.json"),
        ]
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with config_path.open("r", encoding="utf-8") as handle:
                        loaded = json.load(handle)
                    self._config.update(loaded)
                    self._config_sources[str(config_path)] = str(config_path)
                    _logger.debug(f"Loaded configuration from {config_path}")
                except Exception as e:
                    _logger.warning(f"Failed to load config from {config_path}: {e}")

        if self._config:
            self._config_sources["runtime_overrides"] = "runtime_overrides"

        # Load from workspace configuration
        workspace_path = os.getenv("TANGKU_AGENTOS_WORKSPACE") or \
            "/workspaces/TangkuAgentOS"
        workspace_config = Path(workspace_path) / "workspace.json"
        if workspace_config.exists():
            try:
                with workspace_config.open("r", encoding="utf-8") as handle:
                    workspace_values = json.load(handle)
                self._config.update(workspace_values)
                self._config_sources[str(workspace_config)] = str(workspace_config)
                _logger.debug(f"Loaded workspace config from {workspace_config}")
            except Exception as e:
                _logger.warning(f"Failed to load workspace config: {e}")

    def _config_value(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by its key.

        Args:
            key: The configuration key.
            default: The default value to return if the key is not found.

        Returns:
            The configuration value, or the default value if the key is not found.
        """
        return self._config.get(key, default)

    # -------------------------------------------------------------------------- #
    # Internal Methods: State and Observability
    # -------------------------------------------------------------------------- #

    def _persist_state(self, phase: str) -> None:
        """Persists the kernel state for a given phase.

        Args:
            phase: The phase of the kernel lifecycle (e.g., "startup", "shutdown").
        """
        self.state_manager.set_state(
            "kernel",
            {"phase": phase, "kernel_id": self._kernel_id, "config": dict(self._config)},
        )
        self.snapshots.create_snapshot(
            f"snapshot-{phase}", {"phase": phase, "kernel_id": self._kernel_id}
        )
        _logger.debug(f"Persisted kernel state for phase: {phase}")

    def _record_observability(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Records an observability event.

        Args:
            event_name: The name of the event to record.
            payload: The payload to include with the event.
        """
        try:
            self._event_bus.publish(event_name, payload)
        except Exception as e:
            _logger.warning(f"Failed to publish event {event_name}: {e}")

        try:
            if (
                self._observability_manager is not None
                and hasattr(self._observability_manager, "event_recorder")
            ):
                self._observability_manager.event_recorder.record(
                    {"event": event_name, "payload": payload}
                )
        except Exception as e:
            _logger.warning(f"Failed to record observability event: {e}")

    def _register_internal_services(self) -> None:
        """Registers internal services with the kernel.

        This method registers the event bus, memory manager, security manager,
        observability manager, and configuration as singleton services.
        """
        self.register_singleton("event_bus", self._event_bus)
        self.register_singleton("memory", self._memory_manager)
        self.register_singleton("security", self._security_manager)
        self.register_singleton("observability", self._observability_manager)
        self.register_singleton("configuration", self._config)
        _logger.debug("Registered internal services")
