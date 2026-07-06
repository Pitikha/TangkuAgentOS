from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    ArchitectureGraph,
    File,
    Module,
    Project,
    ProjectSnapshot,
    Workspace,
    WorkspaceConfiguration,
    WorkspaceMetadata,
    WorkspaceSnapshot,
)


class WorkspaceRegistryInterface(ABC):
    """Interface for workspace registry operations."""

    @abstractmethod
    def register(self, workspace: Workspace) -> None:
        ...

    @abstractmethod
    def get(self, workspace_id: str) -> Workspace:
        ...

    @abstractmethod
    def list(self) -> list[Workspace]:
        ...


class WorkspaceManagerInterface(ABC):
    """Interface for workspace orchestration."""

    @abstractmethod
    def create_workspace(self, workspace: Workspace) -> None:
        ...

    @abstractmethod
    def get_workspace(self, workspace_id: str) -> Workspace:
        ...

    @abstractmethod
    def list_workspaces(self) -> list[Workspace]:
        ...


class WorkspaceContextInterface(ABC):
    """Interface for workspace contexts."""

    @abstractmethod
    def build_context(self, workspace: Workspace) -> dict[str, str]:
        ...


class WorkspaceScannerInterface(ABC):
    """Interface for scanning workspace files."""

    @abstractmethod
    def scan(self, workspace: Workspace) -> None:
        ...


class WorkspaceIndexerInterface(ABC):
    """Interface for workspace indexing."""

    @abstractmethod
    def index(self, workspace: Workspace) -> None:
        ...


class ArchitectureAnalyzerInterface(ABC):
    """Interface for analyzing workspace architecture."""

    @abstractmethod
    def analyze(self, workspace: Workspace) -> ArchitectureGraph:
        ...


class WorkspaceCacheInterface(ABC):
    """Interface for workspace caching."""

    @abstractmethod
    def get(self, context_id: str) -> Workspace | None:
        ...

    @abstractmethod
    def put(self, workspace: Workspace) -> None:
        ...
