from __future__ import annotations

from .interfaces import WorkspaceIndexerInterface
from .models import Workspace


class WorkspaceIndexer(WorkspaceIndexerInterface):
    """Index workspace contents by updating statistics and metadata."""

    def index(self, workspace: Workspace) -> None:
        workspace.statistics.module_count = sum(len(project.packages) for project in workspace.projects)
        workspace.metadata.attributes['indexed'] = True
