"""Dependency management for TangkuAgentOS kernel runtimes.

This module provides the `RuntimeDependencyManager` class, which is responsible
for managing and resolving dependencies between runtimes. It uses a topological
sort algorithm to determine the correct startup order for runtimes based on
their dependencies.
"""

from __future__ import annotations

from collections import deque
from threading import RLock
from typing import Dict, Final, List, Optional


class RuntimeDependencyManager:
    """Manages and resolves dependencies between runtimes.

    This class maintains a graph of runtime dependencies and provides methods
    for adding dependencies, retrieving dependencies for a runtime, and resolving
    the startup order using a topological sort (Kahn's algorithm).

    Attributes:
        _dependencies: A dictionary mapping runtime IDs to their dependency lists.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the dependency manager with an empty dependency graph."""
        self._dependencies: Dict[str, List[str]] = {}
        self._lock: Final[RLock] = RLock()

    def dependencies(self) -> Dict[str, List[str]]:
        """Returns a copy of the current dependency graph.

        Returns:
            A dictionary mapping runtime IDs to their dependency lists.
        """
        with self._lock:
            return {
                runtime_id: list(dependencies)
                for runtime_id, dependencies in self._dependencies.items()
            }

    def add_dependency(self, runtime_id: str, dependency: str) -> None:
        """Adds a dependency for a runtime.

        Args:
            runtime_id: The ID of the runtime that depends on another runtime.
            dependency: The ID of the runtime that is a dependency.
        """
        with self._lock:
            self._dependencies.setdefault(runtime_id, [])
            if dependency not in self._dependencies[runtime_id]:
                self._dependencies[runtime_id].append(dependency)

    def get_dependencies(self, runtime_id: str) -> List[str]:
        """Retrieves the dependencies for a runtime.

        Args:
            runtime_id: The ID of the runtime whose dependencies to retrieve.

        Returns:
            A list of dependency runtime IDs.
        """
        with self._lock:
            return list(self._dependencies.get(runtime_id, []))

    def resolve_startup_order(self, runtime_ids: List[str]) -> List[str]:
        """Resolves the startup order for a list of runtimes based on dependencies.

        This method uses Kahn's algorithm for topological sorting to determine
        the correct order in which runtimes should be started, ensuring that
        dependencies are started before the runtimes that depend on them.

        Args:
            runtime_ids: A list of runtime IDs to resolve the startup order for.

        Returns:
            A list of runtime IDs in the order they should be started.
        """
        # Collect all nodes (runtimes and their dependencies)
        nodes = set(runtime_ids)
        for runtime_id in runtime_ids:
            nodes.update(self.get_dependencies(runtime_id))

        # Initialize in-degree and reverse adjacency list
        indegree: Dict[str, int] = {node: 0 for node in nodes}
        reverse: Dict[str, List[str]] = {node: [] for node in nodes}

        # Build the graph
        for runtime_id in runtime_ids:
            for dependency in self.get_dependencies(runtime_id):
                if dependency in nodes:
                    reverse[dependency].append(runtime_id)
                    indegree[runtime_id] += 1

        # Initialize queue with nodes that have no dependencies
        queue = deque(sorted(node for node in nodes if indegree[node] == 0))
        result: List[str] = []

        # Process nodes in topological order
        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in reverse[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        return result
