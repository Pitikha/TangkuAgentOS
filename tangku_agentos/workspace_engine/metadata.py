from __future__ import annotations

from .models import ProjectMetadata, WorkspaceMetadata


class WorkspaceMetadataManager:
    """Store workspace and project metadata by ID."""

    def __init__(self) -> None:
        self._workspace_metadata: dict[str, WorkspaceMetadata] = {}
        self._project_metadata: dict[str, ProjectMetadata] = {}

    def update_workspace_metadata(self, workspace_id: str, metadata: WorkspaceMetadata) -> None:
        self._workspace_metadata[workspace_id] = metadata

    def update_project_metadata(self, project_id: str, metadata: ProjectMetadata) -> None:
        self._project_metadata[project_id] = metadata

    def get_workspace_metadata(self, workspace_id: str) -> WorkspaceMetadata | None:
        return self._workspace_metadata.get(workspace_id)

    def get_project_metadata(self, project_id: str) -> ProjectMetadata | None:
        return self._project_metadata.get(project_id)
