from __future__ import annotations

from .interfaces import PackageManagerInterface


class PackageManager(PackageManagerInterface):
    """Package manager architecture."""

    def install_package(self, manifest: "PackageManifest") -> None:
        raise NotImplementedError

    def uninstall_package(self, package_id: str) -> None:
        raise NotImplementedError

    def list_packages(self) -> list["PackageMetadata"]:
        raise NotImplementedError
