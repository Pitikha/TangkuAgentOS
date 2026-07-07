from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    ComponentGraph,
    DependencyTree,
    ModuleGraph,
    ProjectGraph,
    Repository,
    ServiceGraph,
)


class ProjectRegistryInterface(ABC):
    """Interface for project intelligence registry."""

    @abstractmethod
    def register(self, repository: Repository) -> None:
        ...

    @abstractmethod
    def resolve(self, repository_id: str) -> Repository:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class ProjectIntelligenceManager(ABC):
    """Interface for project intelligence orchestration."""

    @abstractmethod
    def analyze_project(self, repository_id: str) -> ProjectGraph:
        ...

    @abstractmethod
    def get_project_graph(self, repository_id: str) -> ProjectGraph:
        ...

    @abstractmethod
    def get_dependency_tree(self, repository_id: str) -> DependencyTree:
        ...


class ProjectAnalyzer(ABC):
    @abstractmethod
    def analyze(self, repository: Repository) -> ProjectGraph:
        ...


class DependencyAnalyzer(ABC):
    @abstractmethod
    def analyze_dependencies(self, repository: Repository) -> DependencyTree:
        ...


class ArchitectureAnalyzer(ABC):
    @abstractmethod
    def analyze_architecture(self, repository: Repository) -> ComponentGraph:
        ...


class BuildAnalyzer(ABC):
    @abstractmethod
    def analyze_build(self, repository: Repository) -> dict[str, Any]:
        ...


class FrameworkAnalyzer(ABC):
    @abstractmethod
    def analyze_frameworks(self, repository: Repository) -> dict[str, Any]:
        ...


class PackageAnalyzer(ABC):
    @abstractmethod
    def analyze_packages(self, repository: Repository) -> dict[str, Any]:
        ...


class TestStructureAnalyzer(ABC):
    @abstractmethod
    def analyze_tests(self, repository: Repository) -> dict[str, Any]:
        ...


class DocumentationAnalyzer(ABC):
    @abstractmethod
    def analyze_documentation(self, repository: Repository) -> dict[str, Any]:
        ...


class ConfigurationAnalyzer(ABC):
    @abstractmethod
    def analyze_configuration(self, repository: Repository) -> dict[str, Any]:
        ...


class ProjectSession(ABC):
    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def get_status(self) -> str:
        ...
