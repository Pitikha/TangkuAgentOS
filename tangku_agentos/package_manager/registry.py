from __future__ import annotations

from .interfaces import PackageRegistryInterface


class PackageRegistry(PackageRegistryInterface):
    """Package registry architecture."""

    def register(self, metadata: "PackageMetadata") -> None:
        raise NotImplementedError

    def resolve(self, package_id: str) -> "PackageMetadata":
        raise NotImplementedError
