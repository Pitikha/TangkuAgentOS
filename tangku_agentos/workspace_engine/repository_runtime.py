from __future__ import annotations

from .models import Project


class RepositoryManager:
    """VCS-agnostic repository manager placeholder for later backends."""

    def __init__(self) -> None:
        self._repositories: dict[str, Project] = {}

    def register(self, repository_id: str, project: Project) -> None:
        self._repositories[repository_id] = project

    def get(self, repository_id: str) -> Project:
        repository = self._repositories.get(repository_id)
        if repository is None:
            raise KeyError(repository_id)
        return repository


class BranchManager:
    """Track repository branch names without performing operations."""

    def __init__(self) -> None:
        self._branches: dict[str, list[str]] = {}

    def register(self, repository_id: str, branches: list[str]) -> None:
        self._branches[repository_id] = list(branches)

    def list_branches(self, repository_id: str) -> list[str]:
        return list(self._branches.get(repository_id, []))


class RepositoryContextManager:
    """Provide repository context metadata."""

    def build_context(self, repository_id: str) -> dict[str, str]:
        return {"repository_id": repository_id}


class RepositoryStateManager:
    """Track repository state flags."""

    def __init__(self) -> None:
        self._states: dict[str, str] = {}

    def set_state(self, repository_id: str, state: str) -> None:
        self._states[repository_id] = state

    def get_state(self, repository_id: str) -> str | None:
        return self._states.get(repository_id)
