from __future__ import annotations

from abc import ABC, abstractmethod

from .models import PackageManifest, PackageMetadata


class PackageManagerInterface(ABC):
    """Interface for package manager."""

    @abstractmethod
    def install_package(self, manifest: PackageManifest) -> None:
        ...

    @abstractmethod
    def uninstall_package(self, package_id: str) -> None:
        ...

    @abstractmethod
    def list_packages(self) -> list[PackageMetadata]:
        ...


class PackageRegistryInterface(ABC):
    """Interface for package registry."""

    @abstractmethod
    def register(self, metadata: PackageMetadata) -> None:
        ...

    @abstractmethod
    def resolve(self, package_id: str) -> PackageMetadata:
        ...


class PackageResolver(ABC):
    """Interface for package resolution."""

    @abstractmethod
    def resolve(self, package_id: str, version: str | None = None) -> PackageManifest:
        ...
