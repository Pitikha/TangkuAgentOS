from __future__ import annotations

import copy
import json
import time
from threading import RLock
from typing import Any, Dict, List, Optional, Type

from .exceptions import (
    RollbackError,
    SerializationError,
    StateError,
    StateKeyNotFoundError,
    TransactionError,
)
from .types import (
    Metadata,
    StateData,
    StateSnapshot,
    StateChangeType,
    StorageBackend,
)


class InMemoryStorageBackend:
    """Default in-memory storage backend for state snapshots."""

    def __init__(self) -> None:
        self._snapshots: List[StateSnapshot] = []
        self._lock = RLock()

    def save(self, snapshot: StateSnapshot) -> None:
        """Save a state snapshot."""
        with self._lock:
            self._snapshots.append(snapshot)

    def load(self) -> Optional[StateSnapshot]:
        """Load the latest state snapshot."""
        with self._lock:
            return copy.deepcopy(self._snapshots[-1]) if self._snapshots else None

    def list_snapshots(self) -> List[StateSnapshot]:
        """List all available snapshots."""
        with self._lock:
            return copy.deepcopy(self._snapshots)


class StateManager:
    """
    Production-grade state manager with:
    - Persistent storage abstraction
    - Snapshot versioning
    - Transaction support
    - Rollback
    - Recovery
    - Serialization
    - Import/export
    - Change tracking
    """

    def __init__(self, storage_backend: Optional[StorageBackend] = None) -> None:
        self._state: StateData = {}
        self._metadata: Metadata = {}
        self._history: List[StateSnapshot] = []
        self._lock = RLock()
        self._storage_backend = storage_backend or InMemoryStorageBackend()
        self._transaction_stack: List[Dict[str, Any]] = []
        self._change_tracking = True

    # --- State Operations ---
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        with self._lock:
            return self._state.get(key, default)

    def set(
        self,
        key: str,
        value: Any,
        metadata: Metadata | None = None,
        track_change: bool = True,
    ) -> None:
        """Set a value in the state."""
        if not key:
            raise StateError("State key must be provided.")

        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
            if metadata is not None:
                self._metadata[key] = metadata
            if track_change:
                self._record_change(StateChangeType.UPDATED, key, old_value, value)

    def remove(self, key: str, track_change: bool = True) -> None:
        """Remove a value from the state."""
        with self._lock:
            if key not in self._state:
                raise StateKeyNotFoundError(f"State key not found: {key}")
            old_value = self._state[key]
            del self._state[key]
            self._metadata.pop(key, None)
            if track_change:
                self._record_change(StateChangeType.REMOVED, key, old_value, None)

    def reset(self, track_change: bool = True) -> None:
        """Reset the state to empty."""
        with self._lock:
            old_state = self._state.copy()
            self._state.clear()
            self._metadata.clear()
            if track_change:
                for key, value in old_state.items():
                    self._record_change(StateChangeType.REMOVED, key, value, None)

    # --- Snapshots ---
    def snapshot(self, version: Optional[int] = None) -> StateSnapshot:
        """Create a snapshot of the current state."""
        with self._lock:
            snapshot = StateSnapshot(
                state=copy.deepcopy(self._state),
                metadata=copy.deepcopy(self._metadata),
                timestamp=time.time(),
                version=version or (self._history[-1].version + 1 if self._history else 1),
            )
            self._history.append(snapshot)
            self._storage_backend.save(snapshot)
            return snapshot

    def restore(self, snapshot: StateSnapshot) -> None:
        """Restore the state from a snapshot."""
        if snapshot is None:
            raise StateError("Snapshot must be provided for restore.")

        with self._lock:
            self._state = copy.deepcopy(snapshot.state)
            self._metadata = copy.deepcopy(snapshot.metadata)
            self._record_change(StateChangeType.RESTORED)

    def list_snapshots(self) -> List[StateSnapshot]:
        """List all available snapshots."""
        with self._lock:
            return copy.deepcopy(self._history)

    def get_latest_snapshot(self) -> Optional[StateSnapshot]:
        """Get the latest snapshot."""
        with self._lock:
            return copy.deepcopy(self._history[-1]) if self._history else None

    # --- Transactions ---
    def begin_transaction(self) -> None:
        """Begin a new transaction."""
        with self._lock:
            self._transaction_stack.append(copy.deepcopy(self._state))

    def commit(self) -> None:
        """Commit the current transaction."""
        with self._lock:
            if not self._transaction_stack:
                raise TransactionError("No active transaction to commit.")
            self._transaction_stack.pop()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        with self._lock:
            if not self._transaction_stack:
                raise RollbackError("No active transaction to rollback.")
            self._state = self._transaction_stack.pop()
            self._record_change(StateChangeType.ROLLBACK)

    def transaction_depth(self) -> int:
        """Get the current transaction depth."""
        with self._lock:
            return len(self._transaction_stack)

    # --- Serialization ---
    def serialize(self, snapshot: Optional[StateSnapshot] = None) -> str:
        """Serialize a snapshot to JSON."""
        target = snapshot or self.get_latest_snapshot()
        if target is None:
            raise SerializationError("No snapshot to serialize.")
        try:
            return json.dumps(
                {
                    "state": target.state,
                    "metadata": target.metadata,
                    "timestamp": target.timestamp,
                    "version": target.version,
                }
            )
        except Exception as e:
            raise SerializationError(f"Failed to serialize snapshot: {e}") from e

    def deserialize(self, serialized: str) -> StateSnapshot:
        """Deserialize a snapshot from JSON."""
        try:
            data = json.loads(serialized)
            return StateSnapshot(
                state=data.get("state", {}),
                metadata=data.get("metadata", {}),
                timestamp=data.get("timestamp", 0.0),
                version=data.get("version", 1),
            )
        except Exception as e:
            raise SerializationError(f"Failed to deserialize snapshot: {e}") from e

    # --- Import/Export ---
    def export_state(self) -> Dict[str, Any]:
        """Export the current state and metadata as a dictionary."""
        with self._lock:
            return {
                "state": copy.deepcopy(self._state),
                "metadata": copy.deepcopy(self._metadata),
            }

    def import_state(self, data: Dict[str, Any]) -> None:
        """Import state and metadata from a dictionary."""
        with self._lock:
            self._state = copy.deepcopy(data.get("state", {}))
            self._metadata = copy.deepcopy(data.get("metadata", {}))
            self._record_change(StateChangeType.CREATED)

    # --- Recovery ---
    def recover_from_storage(self) -> bool:
        """Recover the state from the storage backend. Returns True if successful."""
        snapshot = self._storage_backend.load()
        if snapshot is not None:
            self.restore(snapshot)
            return True
        return False

    # --- Change Tracking ---
    def enable_change_tracking(self) -> None:
        """Enable change tracking."""
        self._change_tracking = True

    def disable_change_tracking(self) -> None:
        """Disable change tracking."""
        self._change_tracking = False

    def _record_change(
        self,
        change_type: StateChangeType,
        key: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None,
    ) -> None:
        """Record a state change."""
        if not self._change_tracking:
            return
        with self._lock:
            snapshot = StateSnapshot(
                state=copy.deepcopy(self._state),
                metadata=copy.deepcopy(self._metadata),
                timestamp=time.time(),
                version=self._history[-1].version + 1 if self._history else 1,
            )
            snapshot.metadata["_change_type"] = change_type
            if key:
                snapshot.metadata["_changed_key"] = key
            if old_value is not None:
                snapshot.metadata["_old_value"] = old_value
            if new_value is not None:
                snapshot.metadata["_new_value"] = new_value
            self._history.append(snapshot)

    # --- Utility ---
    def list_keys(self) -> List[str]:
        """List all keys in the state."""
        with self._lock:
            return list(self._state.keys())

    def contains(self, key: str) -> bool:
        """Check if a key exists in the state."""
        with self._lock:
            return key in self._state

    def as_dict(self) -> StateData:
        """Get the current state as a dictionary."""
        with self._lock:
            return copy.deepcopy(self._state)

    def history(self) -> List[StateSnapshot]:
        """Get the history of state snapshots."""
        with self._lock:
            return copy.deepcopy(self._history)

    def clear_history(self) -> None:
        """Clear the state history."""
        with self._lock:
            self._history.clear()
