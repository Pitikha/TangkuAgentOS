"""Runtime supervision for TangkuAgentOS kernel.

This module provides the `RuntimeSupervisor` class, which is responsible for
monitoring and managing the state of individual runtimes within the kernel.
It ensures thread-safe operations for runtime registration, unregistration,
and state transitions.
"""

from __future__ import annotations

from threading import RLock
from typing import Dict, Final, Optional

from .types import KernelRuntime


class RuntimeSupervisor:
    """Supervises the lifecycle and state of runtimes in the kernel.

    This class maintains a registry of runtimes and provides thread-safe
    operations for managing their state (e.g., starting, stopping, restarting).

    Attributes:
        _runtimes: A dictionary mapping runtime IDs to their `KernelRuntime` objects.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the runtime supervisor with an empty runtime registry."""
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._lock: Final[RLock] = RLock()

    def register_runtime(self, runtime: KernelRuntime) -> None:
        """Registers a runtime with the supervisor.

        Args:
            runtime: The `KernelRuntime` object to register.
        """
        with self._lock:
            self._runtimes[runtime.runtime_id] = runtime

    def unregister_runtime(self, runtime_id: str) -> None:
        """Unregisters a runtime from the supervisor.

        Args:
            runtime_id: The ID of the runtime to unregister.
        """
        with self._lock:
            self._runtimes.pop(runtime_id, None)

    def get_runtime(self, runtime_id: str) -> Optional[KernelRuntime]:
        """Retrieves a runtime by its ID.

        Args:
            runtime_id: The ID of the runtime to retrieve.

        Returns:
            The `KernelRuntime` object if found, otherwise `None`.
        """
        with self._lock:
            return self._runtimes.get(runtime_id)

    def start_runtime(self, runtime_id: str) -> str:
        """Starts a runtime and updates its status to 'running'.

        Args:
            runtime_id: The ID of the runtime to start.

        Returns:
            The new status of the runtime, or "unknown" if the runtime was not found.
        """
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
        """Shuts down a runtime and updates its status to 'stopped'.

        Args:
            runtime_id: The ID of the runtime to shut down.

        Returns:
            The new status of the runtime, or "unknown" if the runtime was not found.
        """
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
        """Restarts a runtime by starting it again.

        Args:
            runtime_id: The ID of the runtime to restart.

        Returns:
            The new status of the runtime.
        """
        return self.start_runtime(runtime_id)

    def monitor_runtime(self, runtime_id: str) -> str:
        """Monitors the current status of a runtime.

        Args:
            runtime_id: The ID of the runtime to monitor.

        Returns:
            The current status of the runtime, or "unknown" if the runtime was not found.
        """
        with self._lock:
            runtime = self._runtimes.get(runtime_id)
            return runtime.status if runtime is not None else "unknown"
