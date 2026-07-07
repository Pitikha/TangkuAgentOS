from __future__ import annotations

from typing import Dict

from .exceptions import WorkspaceRegistryError
from .interfaces import WorkspaceRegistryInterface
from .models import Workspace


class WorkspaceRegistry(WorkspaceRegistryInterface):
    """Registry for workspace definitions."""

    def __init__(self) -> None:
        self._workspaces: Dict[str, Workspace] = {}

    def register(self, workspace: Workspace) -> None:
        self._workspaces[workspace.workspace_id] = workspace

    def get(self, workspace_id: str) -> Workspace:
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise WorkspaceRegistryError(f'Workspace not found: {workspace_id}')
        return workspace

    def unregister(self, workspace_id: str) -> None:
        if workspace_id not in self._workspaces:
            raise WorkspaceRegistryError(f'Workspace not found: {workspace_id}')
        del self._workspaces[workspace_id]

    def list(self) -> list[Workspace]:
        return list(self._workspaces.values())
