from __future__ import annotations

from .models import Project, ProjectMetadata, ProjectSnapshot, ProjectStatistics


class ProjectManager:
    """Manage projects and their metadata within a workspace."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    def create_project(self, project: Project) -> None:
        self._projects[project.project_id] = project

    def get_project(self, project_id: str) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        return project

    def list_projects(self) -> list[Project]:
        return list(self._projects.values())


class ProjectRegistry:
    """Registry for project instances."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    def register(self, project: Project) -> None:
        self._projects[project.project_id] = project

    def get(self, project_id: str) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise KeyError(project_id)
        return project

    def list(self) -> list[Project]:
        return list(self._projects.values())


class ProjectLoader:
    """Create a project object from a path and metadata."""

    def load(self, path: str, name: str | None = None) -> Project:
        project_name = name or path.split('/')[-1] or 'project'
        return Project(project_id=project_name, name=project_name, path=path)


class ProjectMetadataManager:
    """Track project metadata updates."""

    def __init__(self) -> None:
        self._metadata: dict[str, ProjectMetadata] = {}

    def update(self, project_id: str, metadata: ProjectMetadata) -> None:
        self._metadata[project_id] = metadata

    def get(self, project_id: str) -> ProjectMetadata | None:
        return self._metadata.get(project_id)


class ProjectConfigurationManager:
    """Store project-specific configuration."""

    def __init__(self) -> None:
        self._configurations: dict[str, dict[str, object]] = {}

    def get_configuration(self, project_id: str) -> dict[str, object]:
        return dict(self._configurations.get(project_id, {}))

    def set_configuration(self, project_id: str, configuration: dict[str, object]) -> None:
        self._configurations[project_id] = dict(configuration)


class ProjectSnapshotManager:
    """Create snapshot descriptors for projects."""

    def snapshot(self, project: Project) -> ProjectSnapshot:
        return ProjectSnapshot(snapshot_id=f"{project.project_id}-snapshot", project_id=project.project_id, metadata=project.metadata)


class ProjectContextManager:
    """Build a simple context dictionary for a project."""

    def build_context(self, project: Project) -> dict[str, str]:
        return {"project_id": project.project_id, "path": project.path, "name": project.name}


class ProjectStatisticsManager:
    """Collect simple project statistics."""

    def __init__(self) -> None:
        self._stats: dict[str, ProjectStatistics] = {}

    def statistics(self, project_id: str) -> ProjectStatistics:
        return self._stats.get(project_id, ProjectStatistics())

    def update(self, project_id: str, statistics: ProjectStatistics) -> None:
        self._stats[project_id] = statistics
