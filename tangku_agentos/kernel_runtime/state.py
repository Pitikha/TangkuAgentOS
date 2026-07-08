"""State management for TangkuAgentOS kernel runtimes.

This module provides classes for managing the state of the kernel and its runtimes,
including state persistence, snapshots, and recovery.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Final, List, Optional


class SystemStateManager:
    """Manages the system state of the kernel.

    This class provides methods for setting, retrieving, and resetting the state
    of the kernel and its components. It ensures thread-safe state updates.

    Attributes:
        _state: A dictionary mapping component names to their state data.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the system state manager with an empty state dictionary."""
        self._state: Dict[str, Any] = {}
        self._lock: Final[RLock] = RLock()

    def set_state(self, component: str, state: Dict[str, Any]) -> None:
        """Sets the state for a component.

        Args:
            component: The name of the component.
            state: The state data to set for the component.
        """
        with self._lock:
            self._state[component] = state

    def get_state(self, component: str) -> Optional[Dict[str, Any]]:
        """Retrieves the state for a component.

        Args:
            component: The name of the component.

        Returns:
            The state data if found, otherwise `None`.
        """
        with self._lock:
            return self._state.get(component)

    def reset_state(self, component: str) -> None:
        """Resets the state for a component.

        Args:
            component: The name of the component.
        """
        with self._lock:
            self._state.pop(component, None)


class RuntimeStateRegistry:
    """Registry for tracking the state of individual runtimes.

    This class maintains a registry of runtime states and provides thread-safe
    operations for updating and retrieving runtime states.

    Attributes:
        _states: A dictionary mapping runtime IDs to their state strings.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the runtime state registry with an empty state dictionary."""
        self._states: Dict[str, str] = {}
        self._lock: Final[RLock] = RLock()

    def set_state(self, runtime_id: str, state: str) -> None:
        """Sets the state for a runtime.

        Args:
            runtime_id: The ID of the runtime.
            state: The state string to set (e.g., "running", "stopped").
        """
        with self._lock:
            self._states[runtime_id] = state

    def get_state(self, runtime_id: str) -> Optional[str]:
        """Retrieves the state for a runtime.

        Args:
            runtime_id: The ID of the runtime.

        Returns:
            The state string if found, otherwise `None`.
        """
        with self._lock:
            return self._states.get(runtime_id)

    def reset_state(self, runtime_id: str) -> None:
        """Resets the state for a runtime.

        Args:
            runtime_id: The ID of the runtime.
        """
        with self._lock:
            self._states.pop(runtime_id, None)


class SystemSnapshotManager:
    """Manages system state snapshots for the kernel.

    This class provides methods for creating, retrieving, and restoring
    snapshots of the kernel's state. It ensures thread-safe snapshot operations.

    Attributes:
        _snapshots: A dictionary mapping snapshot IDs to their data.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the snapshot manager with an empty snapshot dictionary."""
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._lock: Final[RLock] = RLock()

    def create_snapshot(self, snapshot_id: str, data: Dict[str, Any]) -> None:
        """Creates a new snapshot.

        Args:
            snapshot_id: The ID of the snapshot.
            data: The data to store in the snapshot.
        """
        with self._lock:
            self._snapshots[snapshot_id] = data

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a snapshot by its ID.

        Args:
            snapshot_id: The ID of the snapshot to retrieve.

        Returns:
            The snapshot data if found, otherwise `None`.
        """
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Restores a snapshot by its ID.

        Args:
            snapshot_id: The ID of the snapshot to restore.

        Returns:
            The restored snapshot data if found, otherwise `None`.
        """
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def delete_snapshot(self, snapshot_id: str) -> None:
        """Deletes a snapshot by its ID.

        Args:
            snapshot_id: The ID of the snapshot to delete.
        """
        with self._lock:
            self._snapshots.pop(snapshot_id, None)
