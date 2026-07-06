from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Artifact, ArtifactMetadata, ArtifactRelationship, ArtifactVersion


class ArtifactManager(ABC):
    """Interface for managing generated artifacts."""

    @abstractmethod
    def register_artifact(self, artifact: Artifact) -> None:
        ...

    @abstractmethod
    def get_artifact(self, artifact_id: str) -> Artifact:
        ...

    @abstractmethod
    def list_artifacts(self) -> list[Artifact]:
        ...


class ArtifactRegistry(ABC):
    """Interface for artifact registry operations."""

    @abstractmethod
    def register(self, artifact: Artifact) -> None:
        ...

    @abstractmethod
    def resolve(self, artifact_id: str) -> Artifact:
        ...

    @abstractmethod
    def list(self) -> list[Artifact]:
        ...
