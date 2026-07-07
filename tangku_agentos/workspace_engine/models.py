from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class WorkspaceStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ARCHIVED = 'archived'


@dataclass(frozen=True)
class WorkspaceMetadata:
    workspace_id: str
    name: str
    description: str = ''
    root_path: str = ''
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceStatistics:
    file_count: int = 0
    project_count: int = 0
    module_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceConfiguration:
    watch_enabled: bool = False
    language_detection: bool = True
    framework_detection: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceSnapshot:
    snapshot_id: str
    workspace_id: str
    metadata: WorkspaceMetadata = field(default_factory=lambda: WorkspaceMetadata(workspace_id='', name=''))


@dataclass
class ProjectMetadata:
    project_id: str
    name: str
    description: str = ''
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectStatistics:
    module_count: int = 0
    file_count: int = 0
    dependency_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectSnapshot:
    snapshot_id: str
    project_id: str
    metadata: ProjectMetadata = field(default_factory=lambda: ProjectMetadata(project_id='', name=''))


@dataclass
class Project:
    project_id: str
    name: str
    path: str
    packages: List['Package'] = field(default_factory=list)
    metadata: ProjectMetadata = field(default_factory=lambda: ProjectMetadata(project_id='', name=''))
    statistics: ProjectStatistics = field(default_factory=ProjectStatistics)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    root_path: str
    projects: List[Project] = field(default_factory=list)
    metadata: WorkspaceMetadata = field(default_factory=lambda: WorkspaceMetadata(workspace_id='', name=''))
    statistics: WorkspaceStatistics = field(default_factory=WorkspaceStatistics)


@dataclass
class Package:
    package_id: str
    name: str
    path: str
    modules: List['Module'] = field(default_factory=list)


@dataclass
class Module:
    module_id: str
    name: str
    path: str
    files: List['File'] = field(default_factory=list)


@dataclass
class Directory:
    directory_id: str
    path: str
    files: List['File'] = field(default_factory=list)
    subdirectories: List['Directory'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileIndex:
    index_id: str
    file: File
    symbols: List['Symbol'] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class File:
    file_id: str
    path: str
    content_type: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Symbol:
    symbol_id: str
    name: str
    symbol_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dependency:
    source: str
    target: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportGraph:
    graph_id: str
    nodes: List[File] = field(default_factory=list)
    edges: List[Dependency] = field(default_factory=list)


@dataclass
class ArchitectureGraph:
    graph_id: str
    nodes: List[Module] = field(default_factory=list)
    edges: List[Dependency] = field(default_factory=list)
