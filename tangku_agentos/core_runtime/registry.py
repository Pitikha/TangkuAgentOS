from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Iterable, List, Optional

from .constants import RegistryScope
from .exceptions import RegistryError
from .types import Metadata, RegistryEntry, RegistryKey, RegistryValue


class Registry:
    """Core registry for tracking shared kernel resources."""

    def __init__(self) -> None:
        self._entries: Dict[str, RegistryEntry] = {}
        self._lock = RLock()

    def register(
        self,
        key: RegistryKey,
        value: RegistryValue,
        scope: RegistryScope = RegistryScope.GLOBAL,
        metadata: Metadata | None = None,
        overwrite: bool = False,
    ) -> None:
        if not key:
            raise RegistryError("Registry key must be defined.")

        with self._lock:
            if key in self._entries and not overwrite:
                raise RegistryError(f"Registry entry already exists: {key}")
            self._entries[key] = RegistryEntry(
                key=key,
                value=value,
                scope=scope.value,
                metadata=metadata or {},
            )

    def resolve(self, key: RegistryKey) -> RegistryValue:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                raise RegistryError(f"Registry entry not found: {key}")
            return entry.value

    def unregister(self, key: RegistryKey) -> None:
        with self._lock:
            if key not in self._entries:
                raise RegistryError(f"Registry entry not found: {key}")
            del self._entries[key]

    def list_entries(self, scope: RegistryScope | None = None) -> List[RegistryEntry]:
        with self._lock:
            entries = list(self._entries.values())
            if scope is None:
                return entries
            return [entry for entry in entries if entry.scope == scope.value]

    def contains(self, key: RegistryKey) -> bool:
        with self._lock:
            return key in self._entries

    def clear_scope(self, scope: RegistryScope) -> None:
        with self._lock:
            self._entries = {
                key: entry for key, entry in self._entries.items() if entry.scope != scope.value
            }

    def metadata(self, key: RegistryKey) -> Metadata:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                raise RegistryError(f"Registry entry not found: {key}")
            return entry.metadata.copy()
