from __future__ import annotations

from typing import Dict

from .interfaces import ProjectRegistryInterface
from .models import Repository


class ProjectRegistry(ProjectRegistryInterface):
    """Registry for project intelligence repositories."""

    def __init__(self) -> None:
        self._repositories: Dict[str, Repository] = {}

    def register(self, repository: Repository) -> None:
        self._repositories[repository.repository_id] = repository

    def resolve(self, repository_id: str) -> Repository:
        return self._repositories[repository_id]

    def list_registered(self) -> list[str]:
        return list(self._repositories.keys())
