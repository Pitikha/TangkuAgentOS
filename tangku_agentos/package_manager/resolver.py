from __future__ import annotations

from .interfaces import PackageResolver


class PackageResolver(PackageResolver):
    """Package resolver architecture."""

    def resolve(self, package_id: str, version: str | None = None) -> "PackageManifest":
        raise NotImplementedError
