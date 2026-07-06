from __future__ import annotations

from .models import ProjectStatistics, WorkspaceStatistics


class WorkspaceStatisticsManager:
    """Track workspace and project statistics in memory."""

    def __init__(self) -> None:
        self._workspace_statistics: dict[str, WorkspaceStatistics] = {}
        self._project_statistics: dict[str, ProjectStatistics] = {}

    def statistics(self, workspace_id: str) -> WorkspaceStatistics:
        return self._workspace_statistics.get(workspace_id, WorkspaceStatistics())

    def project_statistics(self, project_id: str) -> ProjectStatistics:
        return self._project_statistics.get(project_id, ProjectStatistics())

    def update_workspace_statistics(self, workspace_id: str, statistics: WorkspaceStatistics) -> None:
        self._workspace_statistics[workspace_id] = statistics

    def update_project_statistics(self, project_id: str, statistics: ProjectStatistics) -> None:
        self._project_statistics[project_id] = statistics
