from __future__ import annotations

from .interfaces import WorkspaceScannerInterface
from .models import Workspace


class WorkspaceScanner(WorkspaceScannerInterface):
    """Record workspace scan results via the workspace metadata and statistics."""

    def scan(self, workspace: Workspace) -> None:
        workspace.statistics.file_count = max(workspace.statistics.file_count, len(workspace.projects) * 2)
        workspace.statistics.project_count = len(workspace.projects)
        workspace.metadata.attributes['last_scan'] = 'workspace-scanner'
