"""Runtime registry for TangkuAgentOS kernel.

This module provides the `RuntimeRegistry` class, which maintains a registry
of runtimes and provides thread-safe operations for registration, unregistration,
and retrieval.
"""

from __future__ import annotations

from threading import RLock
from typing import Dict, Final, List, Optional

from .types import KernelRuntime


class RuntimeRegistry:
    """Maintains a registry of runtimes in the kernel.

    This class provides thread-safe operations for registering, unregistering,
    and retrieving runtimes. It ensures that runtime IDs are unique and
    that operations are atomic.

    Attributes:
        _runtimes: A dictionary mapping runtime IDs to their `KernelRuntime` objects.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the runtime registry with an empty dictionary."""
        self._runtimes: Dict[str, KernelRuntime] = {}
        self._lock: Final[RLock] = RLock()

    def register(self, runtime: KernelRuntime) -> None:
        """Registers a runtime in the registry.

        Args:
            runtime: The `KernelRuntime` object to register.
        """
        with self._lock:
            self._runtimes[runtime.runtime_id] = runtime

    def unregister(self, runtime_id: str) -> None:
        """Unregisters a runtime from the registry.

        Args:
            runtime_id: The ID of the runtime to unregister.
        """
        with self._lock:
            self._runtimes.pop(runtime_id, None)

    def get(self, runtime_id: str) -> Optional[KernelRuntime]:
        """Retrieves a runtime by its ID.

        Args:
            runtime_id: The ID of the runtime to retrieve.

        Returns:
            The `KernelRuntime` object if found, otherwise `None`.
        """
        with self._lock:
            return self._runtimes.get(runtime_id)

    def list(self) -> List[KernelRuntime]:
        """Lists all registered runtimes.

        Returns:
            A list of all `KernelRuntime` objects in the registry.
        """
        with self._lock:
            return list(self._runtimes.values())
