from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List


@dataclass(frozen=True)
class PackageDefinition:
    package_id: str
    version: str = "0.1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


class PackageManager:
    def __init__(self) -> None:
        self._packages: Dict[str, PackageDefinition] = {}
        self._lock = RLock()

    def install(self, package_id: str, version: str = "0.1.0", metadata: dict[str, Any] | None = None) -> PackageDefinition:
        with self._lock:
            package = PackageDefinition(package_id=package_id, version=version, metadata=metadata or {})
            self._packages[package_id] = package
            return package


class PackageRegistry:
    def __init__(self) -> None:
        self._packages: Dict[str, PackageDefinition] = {}
        self._lock = RLock()

    def register(self, package: PackageDefinition) -> None:
        with self._lock:
            self._packages[package.package_id] = package


class PackageInstaller:
    def __init__(self) -> None:
        self._installed: Dict[str, PackageDefinition] = {}
        self._lock = RLock()

    def install(self, package: PackageDefinition) -> PackageDefinition:
        with self._lock:
            self._installed[package.package_id] = package
            return package


class PackageResolver:
    def __init__(self) -> None:
        self._packages: Dict[str, PackageDefinition] = {}
        self._lock = RLock()

    def resolve(self, package_id: str) -> PackageDefinition | None:
        with self._lock:
            return self._packages.get(package_id)


class PackageValidator:
    def __init__(self) -> None:
        self._lock = RLock()

    def validate(self, package: PackageDefinition) -> bool:
        with self._lock:
            return package.version != ""
