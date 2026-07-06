from __future__ import annotations

from typing import Dict

from .interfaces import ProjectIntelligenceManager as ProjectIntelligenceManagerInterface
from .models import DependencyTree, ProjectGraph
from .registry import ProjectRegistry


class ProjectIntelligenceManager(ProjectIntelligenceManagerInterface):
    """Manager for project intelligence operations."""

    def __init__(self, registry: ProjectRegistry) -> None:
        self._registry = registry
        self._project_graphs: Dict[str, ProjectGraph] = {}
        self._dependency_trees: Dict[str, DependencyTree] = {}

    def analyze_project(self, repository_id: str) -> ProjectGraph:
        repository = self._registry.resolve(repository_id)
        graph = ProjectGraph(repository_id=repository_id, metadata=repository.metadata.metadata)
        self._project_graphs[repository_id] = graph
        self._dependency_trees[repository_id] = DependencyTree(repository_id=repository_id, root=repository_id)
        return graph

    def get_project_graph(self, repository_id: str) -> ProjectGraph:
        return self._project_graphs[repository_id]

    def get_dependency_tree(self, repository_id: str) -> DependencyTree:
        return self._dependency_trees[repository_id]
