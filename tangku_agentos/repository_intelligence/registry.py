from __future__ import annotations

from typing import Dict

from .interfaces import RepositoryRegistryInterface
from .models import Repository


class RepositoryRegistry(RepositoryRegistryInterface):
    """Registry for repository intelligence artifacts."""

    def __init__(self) -> None:
        self._repositories: Dict[str, Repository] = {}

    def register(self, repository: Repository) -> None:
        self._repositories[repository.repository_id] = repository

    def resolve(self, repository_id: str) -> Repository:
        return self._repositories[repository_id]

    def list_registered(self) -> list[str]:
        return list(self._repositories.keys())
