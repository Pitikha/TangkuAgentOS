from __future__ import annotations

import time
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .constants import RegistryScope
from .exceptions import (
    DuplicateRegistryKeyError,
    LazyLoadingError,
    RegistryError,
    RegistryKeyNotFoundError,
    TTLExpiredError,
)
from .types import Metadata, RegistryEntry, RegistryKey, RegistryValue


class DependencyGraph:
    """Tracks dependencies between registry entries."""

    def __init__(self) -> None:
        self._graph: Dict[RegistryKey, Set[RegistryKey]] = {}
        self._lock = RLock()

    def add_dependency(self, key: RegistryKey, depends_on: RegistryKey) -> None:
        """Add a dependency from `key` to `depends_on`."""
        with self._lock:
            if key not in self._graph:
                self._graph[key] = set()
            self._graph[key].add(depends_on)

    def remove_dependency(self, key: RegistryKey, depends_on: RegistryKey) -> None:
        """Remove a dependency from `key` to `depends_on`."""
        with self._lock:
            if key in self._graph:
                self._graph[key].discard(depends_on)

    def get_dependencies(self, key: RegistryKey) -> Set[RegistryKey]:
        """Get all dependencies for a key."""
        with self._lock:
            return self._graph.get(key, set()).copy()

    def get_dependents(self, key: RegistryKey) -> Set[RegistryKey]:
        """Get all keys that depend on `key`."""
        with self._lock:
            dependents = set()
            for k, deps in self._graph.items():
                if key in deps:
                    dependents.add(k)
            return dependents

    def has_cycle(self) -> bool:
        """Check if the dependency graph has a cycle."""
        with self._lock:
            visited = set()
            recursion_stack = set()

            def _has_cycle(node: RegistryKey) -> bool:
                if node in recursion_stack:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                recursion_stack.add(node)
                for neighbor in self._graph.get(node, set()):
                    if _has_cycle(neighbor):
                        return True
                recursion_stack.remove(node)
                return False

            for node in self._graph:
                if _has_cycle(node):
                    return True
            return False


class Registry:
    """
    Production-grade registry with:
    - TTL support
    - Scoped lifetime
    - Lazy loading
    - Dependency graph
    - Duplicate detection
    - Metrics
    - Health reporting
    - Safe cleanup
    """

    def __init__(self) -> None:
        self._entries: Dict[RegistryKey, RegistryEntry] = {}
        self._lock = RLock()
        self._dependency_graph = DependencyGraph()
        self._metrics = {
            "registrations": 0,
            "resolutions": 0,
            "unregistrations": 0,
            "lazy_loads": 0,
            "ttl_expirations": 0,
        }

    # --- Registration ---
    def register(
        self,
        key: RegistryKey,
        value: RegistryValue,
        scope: RegistryScope = RegistryScope.GLOBAL,
        metadata: Metadata | None = None,
        overwrite: bool = False,
        ttl: Optional[float] = None,
        lazy_loader: Optional[Callable[[], RegistryValue]] = None,
        depends_on: Optional[List[RegistryKey]] = None,
    ) -> None:
        """
        Register a value in the registry.
        Supports TTL, lazy loading, and dependency tracking.
        """
        if not key:
            raise RegistryError("Registry key must be defined.")

        with self._lock:
            if key in self._entries and not overwrite:
                raise DuplicateRegistryKeyError(f"Registry entry already exists: {key}")

            entry = RegistryEntry(
                key=key,
                value=value,
                scope=scope.value,
                metadata=metadata or {},
                ttl=ttl,
                lazy_loader=lazy_loader,
            )
            self._entries[key] = entry
            self._metrics["registrations"] += 1

            if depends_on:
                for dep in depends_on:
                    self._dependency_graph.add_dependency(key, dep)

    # --- Resolution ---
    def resolve(self, key: RegistryKey) -> RegistryValue:
        """
        Resolve a value from the registry.
        Handles lazy loading and TTL expiration.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                raise RegistryKeyNotFoundError(f"Registry entry not found: {key}")

            # Check TTL
            if entry.ttl is not None and entry.ttl > 0:
                if time.time() > entry.metadata.get("_registered_at", time.time()) + entry.ttl:
                    del self._entries[key]
                    self._metrics["ttl_expirations"] += 1
                    raise TTLExpiredError(f"Registry entry '{key}' has expired.")

            # Handle lazy loading
            if entry.lazy_loader is not None and not entry.metadata.get("_loaded", False):
                try:
                    entry.value = entry.lazy_loader()
                    entry.metadata["_loaded"] = True
                    self._metrics["lazy_loads"] += 1
                except Exception as e:
                    raise LazyLoadingError(f"Failed to lazy load '{key}': {e}") from e

            self._metrics["resolutions"] += 1
            return entry.value

    # --- Unregistration ---
    def unregister(self, key: RegistryKey) -> None:
        """Unregister a value from the registry."""
        with self._lock:
            if key not in self._entries:
                raise RegistryKeyNotFoundError(f"Registry entry not found: {key}")
            del self._entries[key]
            self._dependency_graph.remove_dependency(key, key)  # Clean up dependencies
            self._metrics["unregistrations"] += 1

    # --- Scope Management ---
    def list_entries(self, scope: RegistryScope | None = None) -> List[RegistryEntry]:
        """List all entries in the registry, optionally filtered by scope."""
        with self._lock:
            entries = list(self._entries.values())
            if scope is None:
                return entries
            return [entry for entry in entries if entry.scope == scope.value]

    def clear_scope(self, scope: RegistryScope) -> None:
        """Clear all entries in a specific scope."""
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._entries.items() if entry.scope == scope.value
            ]
            for key in keys_to_remove:
                del self._entries[key]
                self._dependency_graph.remove_dependency(key, key)

    # --- Dependency Management ---
    def add_dependency(self, key: RegistryKey, depends_on: RegistryKey) -> None:
        """Add a dependency from `key` to `depends_on`."""
        self._dependency_graph.add_dependency(key, depends_on)

    def get_dependencies(self, key: RegistryKey) -> Set[RegistryKey]:
        """Get all dependencies for a key."""
        return self._dependency_graph.get_dependencies(key)

    def get_dependents(self, key: RegistryKey) -> Set[RegistryKey]:
        """Get all keys that depend on `key`."""
        return self._dependency_graph.get_dependents(key)

    def has_cycle(self) -> bool:
        """Check if the dependency graph has a cycle."""
        return self._dependency_graph.has_cycle()

    # --- Cleanup ---
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns the number of entries removed."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self._entries.items()
                if entry.ttl is not None
                and current_time > entry.metadata.get("_registered_at", current_time) + entry.ttl
            ]
            for key in expired_keys:
                del self._entries[key]
                self._dependency_graph.remove_dependency(key, key)
                self._metrics["ttl_expirations"] += 1
            return len(expired_keys)

    def clear(self) -> None:
        """Clear all entries in the registry."""
        with self._lock:
            self._entries.clear()

    # --- Utility ---
    def contains(self, key: RegistryKey) -> bool:
        """Check if a key exists in the registry."""
        with self._lock:
            return key in self._entries

    def metadata(self, key: RegistryKey) -> Metadata:
        """Get metadata for a registry entry."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                raise RegistryKeyNotFoundError(f"Registry entry not found: {key}")
            return entry.metadata.copy()

    def get_metrics(self) -> Dict[str, int]:
        """Get registry metrics."""
        with self._lock:
            return self._metrics.copy()

    def is_healthy(self) -> bool:
        """Check if the registry is in a healthy state."""
        with self._lock:
            return not self.has_cycle()

    def health_report(self) -> Dict[str, Any]:
        """Generate a health report for the registry."""
        return {
            "healthy": self.is_healthy(),
            "entry_count": len(self._entries),
            "has_cycle": self.has_cycle(),
            "metrics": self.get_metrics(),
        }
