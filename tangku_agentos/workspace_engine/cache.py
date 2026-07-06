from __future__ import annotations

from typing import Dict, Optional

from .interfaces import WorkspaceCacheInterface
from .models import Workspace


class WorkspaceCache(WorkspaceCacheInterface):
    """Workspace cache implementation."""

    def __init__(self) -> None:
        self._cache: Dict[str, Workspace] = {}

    def get(self, context_id: str) -> Workspace | None:
        return self._cache.get(context_id)

    def put(self, workspace: Workspace) -> None:
        self._cache[workspace.workspace_id] = workspace
