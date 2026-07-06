from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class RepositoryMetadata:
    repository_id: str
    name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Repository:
    repository_id: str
    metadata: RepositoryMetadata
    metadata_map: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectGraph:
    repository_id: str
    modules: List["ModuleGraph"] = field(default_factory=list)
    services: List["ServiceGraph"] = field(default_factory=list)
    components: List["ComponentGraph"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModuleGraph:
    module_id: str
    name: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DependencyTree:
    repository_id: str
    root: str
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceGraph:
    service_id: str
    name: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentGraph:
    component_id: str
    name: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
