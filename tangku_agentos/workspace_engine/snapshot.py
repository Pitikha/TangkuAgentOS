from __future__ import annotations

from .models import ProjectSnapshot, WorkspaceSnapshot


class WorkspaceSnapshotManager:
    """Skeleton snapshot manager for workspace and project state."""

    def snapshot_workspace(self, workspace_id: str) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(snapshot_id=f'{workspace_id}-snapshot', workspace_id=workspace_id)

    def snapshot_project(self, project_id: str) -> ProjectSnapshot:
        return ProjectSnapshot(snapshot_id=f'{project_id}-snapshot', project_id=project_id)
