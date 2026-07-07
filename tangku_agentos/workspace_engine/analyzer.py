from __future__ import annotations

from .interfaces import ArchitectureAnalyzerInterface
from .models import ArchitectureGraph, Workspace


class WorkspaceAnalyzer(ArchitectureAnalyzerInterface):
    """Create a lightweight architecture graph from workspace projects."""

    def analyze(self, workspace: Workspace) -> ArchitectureGraph:
        graph = ArchitectureGraph(graph_id=f"analysis-{workspace.workspace_id}")
        for project in workspace.projects:
            for package in project.packages:
                graph.nodes.append(package.modules[0]) if package.modules else None
        return graph
