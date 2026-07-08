"""Resource management for TangkuAgentOS kernel runtimes.

This module provides classes for managing resources, including memory, compute,
and session resources. It ensures that resources are allocated and released
properly to avoid leaks and conflicts.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Final, Optional


class ResourceManager:
    """Manages general resources for the kernel.

    This class provides a centralized interface for managing resources,
    including allocation, release, and monitoring.

    Attributes:
        _resources: A dictionary mapping resource IDs to their data.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the resource manager with an empty resource dictionary."""
        self._resources: Dict[str, Any] = {}
        self._lock: Final[RLock] = RLock()

    def allocate(self, resource_id: str, data: Any) -> None:
        """Allocates a resource.

        Args:
            resource_id: The ID of the resource to allocate.
            data: The data associated with the resource.
        """
        with self._lock:
            self._resources[resource_id] = data

    def release(self, resource_id: str) -> None:
        """Releases a resource.

        Args:
            resource_id: The ID of the resource to release.
        """
        with self._lock:
            self._resources.pop(resource_id, None)

    def get(self, resource_id: str) -> Optional[Any]:
        """Retrieves a resource by its ID.

        Args:
            resource_id: The ID of the resource to retrieve.

        Returns:
            The resource data if found, otherwise `None`.
        """
        with self._lock:
            return self._resources.get(resource_id)


class ResourceRegistry:
    """Registry for tracking resources in the kernel.

    This class maintains a registry of resources and provides thread-safe
    operations for registration, unregistration, and retrieval.

    Attributes:
        _registry: A dictionary mapping resource IDs to their metadata.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the resource registry with an empty dictionary."""
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._lock: Final[RLock] = RLock()

    def register(self, resource_id: str, metadata: Dict[str, Any]) -> None:
        """Registers a resource in the registry.

        Args:
            resource_id: The ID of the resource to register.
            metadata: Metadata associated with the resource.
        """
        with self._lock:
            self._registry[resource_id] = metadata

    def unregister(self, resource_id: str) -> None:
        """Unregisters a resource from the registry.

        Args:
            resource_id: The ID of the resource to unregister.
        """
        with self._lock:
            self._registry.pop(resource_id, None)

    def get_metadata(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata for a resource.

        Args:
            resource_id: The ID of the resource whose metadata to retrieve.

        Returns:
            The metadata if found, otherwise `None`.
        """
        with self._lock:
            return self._registry.get(resource_id)


class MemoryBudgetManager:
    """Manages memory budgets for runtimes.

    This class tracks memory usage and ensures that runtimes do not exceed
    their allocated memory budgets.

    Attributes:
        _budgets: A dictionary mapping runtime IDs to their memory budgets.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the memory budget manager with an empty budget dictionary."""
        self._budgets: Dict[str, int] = {}
        self._lock: Final[RLock] = RLock()

    def set_budget(self, runtime_id: str, budget: int) -> None:
        """Sets the memory budget for a runtime.

        Args:
            runtime_id: The ID of the runtime.
            budget: The memory budget in bytes.
        """
        with self._lock:
            self._budgets[runtime_id] = budget

    def get_budget(self, runtime_id: str) -> int:
        """Retrieves the memory budget for a runtime.

        Args:
            runtime_id: The ID of the runtime.

        Returns:
            The memory budget in bytes, or 0 if not set.
        """
        with self._lock:
            return self._budgets.get(runtime_id, 0)


class ComputeBudgetManager:
    """Manages compute budgets for runtimes.

    This class tracks compute resource usage (e.g., CPU, GPU) and ensures that
    runtimes do not exceed their allocated compute budgets.

    Attributes:
        _budgets: A dictionary mapping runtime IDs to their compute budgets.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the compute budget manager with an empty budget dictionary."""
        self._budgets: Dict[str, Dict[str, int]] = {}
        self._lock: Final[RLock] = RLock()

    def set_budget(self, runtime_id: str, cpu: int, gpu: int = 0) -> None:
        """Sets the compute budget for a runtime.

        Args:
            runtime_id: The ID of the runtime.
            cpu: The CPU budget in units (e.g., cores).
            gpu: The GPU budget in units (e.g., GPUs).
        """
        with self._lock:
            self._budgets[runtime_id] = {"cpu": cpu, "gpu": gpu}

    def get_budget(self, runtime_id: str) -> Dict[str, int]:
        """Retrieves the compute budget for a runtime.

        Args:
            runtime_id: The ID of the runtime.

        Returns:
            A dictionary with "cpu" and "gpu" budgets, or empty if not set.
        """
        with self._lock:
            return self._budgets.get(runtime_id, {"cpu": 0, "gpu": 0})


class SessionResourceManager:
    """Manages resources for individual sessions.

    This class tracks resources allocated to sessions and ensures that
    they are released when the session ends.

    Attributes:
        _sessions: A dictionary mapping session IDs to their resource dictionaries.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the session resource manager with an empty session dictionary."""
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock: Final[RLock] = RLock()

    def create_session(self, session_id: str) -> None:
        """Creates a new session.

        Args:
            session_id: The ID of the session to create.
        """
        with self._lock:
            self._sessions[session_id] = {}

    def release_session(self, session_id: str) -> None:
        """Releases all resources for a session.

        Args:
            session_id: The ID of the session to release.
        """
        with self._lock:
            self._sessions.pop(session_id, None)

    def allocate(self, session_id: str, resource_id: str, data: Any) -> None:
        """Allocates a resource for a session.

        Args:
            session_id: The ID of the session.
            resource_id: The ID of the resource to allocate.
            data: The data associated with the resource.
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {}
            self._sessions[session_id][resource_id] = data

    def release(self, session_id: str, resource_id: str) -> None:
        """Releases a resource for a session.

        Args:
            session_id: The ID of the session.
            resource_id: The ID of the resource to release.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].pop(resource_id, None)
