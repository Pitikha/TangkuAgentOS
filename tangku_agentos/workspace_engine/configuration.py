from __future__ import annotations

from .models import WorkspaceConfiguration


class WorkspaceConfigurationManager:
    """Skeleton workspace configuration manager."""

    def __init__(self) -> None:
        self._configurations: dict[str, WorkspaceConfiguration] = {}

    def get_configuration(self, workspace_id: str) -> WorkspaceConfiguration:
        return self._configurations.get(workspace_id, WorkspaceConfiguration())

    def set_configuration(self, workspace_id: str, configuration: WorkspaceConfiguration) -> None:
        self._configurations[workspace_id] = configuration
