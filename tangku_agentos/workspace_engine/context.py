from __future__ import annotations

from .interfaces import WorkspaceContextInterface
from .models import Workspace


class WorkspaceContext(WorkspaceContextInterface):
    """Workspace context implementation."""

    def build_context(self, workspace: Workspace) -> dict[str, str]:
        return {'workspace_id': workspace.workspace_id}
