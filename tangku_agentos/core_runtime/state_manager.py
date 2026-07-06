from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Iterable, List

from .exceptions import StateError
from .types import Metadata, StateData, StateSnapshot, StateChangeType


class StateManager:
    """Core state manager for managing application state snapshots."""

    def __init__(self) -> None:
        self._state: StateData = {}
        self._metadata: Metadata = {}
        self._history: List[StateSnapshot] = []
        self._lock = RLock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any, metadata: Metadata | None = None) -> None:
        if not key:
            raise StateError("State key must be provided.")

        with self._lock:
            self._state[key] = value
            if metadata is not None:
                self._metadata[key] = metadata
            self._record_change(StateChangeType.UPDATED)

    def remove(self, key: str) -> None:
        with self._lock:
            if key not in self._state:
                raise StateError(f"State key not found: {key}")
            del self._state[key]
            self._metadata.pop(key, None)
            self._record_change(StateChangeType.REMOVED)

    def reset(self) -> None:
        with self._lock:
            self._state.clear()
            self._metadata.clear()
            self._record_change(StateChangeType.RESET)

    def snapshot(self) -> StateSnapshot:
        with self._lock:
            snapshot = StateSnapshot(state=self._state.copy(), metadata=self._metadata.copy())
            self._history.append(snapshot)
            return snapshot

    def restore(self, snapshot: StateSnapshot) -> None:
        if snapshot is None:
            raise StateError("Snapshot must be provided for restore.")

        with self._lock:
            self._state = snapshot.state.copy()
            self._metadata = snapshot.metadata.copy()
            self._record_change(StateChangeType.CREATED)

    def list_keys(self) -> Iterable[str]:
        with self._lock:
            return list(self._state.keys())

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._state

    def history(self) -> List[StateSnapshot]:
        with self._lock:
            return list(self._history)

    def as_dict(self) -> StateData:
        with self._lock:
            return self._state.copy()

    def _record_change(self, change_type: StateChangeType) -> None:
        self._history.append(StateSnapshot(state=self._state.copy(), metadata=self._metadata.copy()))
