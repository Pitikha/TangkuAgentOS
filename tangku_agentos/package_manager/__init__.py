"""Package manager architecture for Tangku AgentOS."""

from .interfaces import (
    PackageManagerInterface,
    PackageRegistryInterface,
    PackageResolver,
)
from .manager import PackageManager
from .registry import PackageRegistry
from .resolver import PackageResolver
from .models import (
    PackageManifest,
    PackageMetadata,
    PackageDependency,
    PackageVersion,
    PackageType,
)

__all__ = [
    "PackageManager",
    "PackageRegistry",
    "PackageResolver",
    "PackageManagerInterface",
    "PackageRegistryInterface",
    "PackageResolver",
    "PackageManifest",
    "PackageMetadata",
    "PackageDependency",
    "PackageVersion",
    "PackageType",
]
