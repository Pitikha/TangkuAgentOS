"""Workspace engine foundation for Tangku AgentOS."""

from .interfaces import (
    ArchitectureAnalyzerInterface,
    WorkspaceCacheInterface,
    WorkspaceContextInterface,
    WorkspaceIndexerInterface,
    WorkspaceManagerInterface,
    WorkspaceRegistryInterface,
    WorkspaceScannerInterface,
)
from .manager import WorkspaceManager
from .registry import WorkspaceRegistry
from .context import WorkspaceContext
from .scanner import WorkspaceScanner
from .indexer import WorkspaceIndexer
from .analyzer import WorkspaceAnalyzer
from .cache import WorkspaceCache
from .configuration import WorkspaceConfigurationManager
from .metadata import WorkspaceMetadataManager
from .statistics import WorkspaceStatisticsManager
from .snapshot import WorkspaceSnapshotManager
from .project_runtime import (
    ProjectConfigurationManager,
    ProjectContextManager,
    ProjectLoader,
    ProjectManager,
    ProjectMetadataManager,
    ProjectRegistry,
    ProjectSnapshotManager,
    ProjectStatisticsManager,
)
from .file_runtime import (
    DirectoryManager,
    FileCache,
    FileIndexManager,
    FileManager,
    FileMetadataManager,
    FileOperationsCoordinator,
    FileWatcher,
)
from .intelligence import (
    ArchitectureGraphManager,
    DependencyGraphManager,
    ImportGraphManager,
    ModuleGraphManager,
    PackageGraphManager,
    RepositoryGraphManager,
    SymbolGraphManager,
)
from .detectors import (
    BuildSystemDetector,
    DetectionRegistry,
    FrameworkDetector,
    LanguageDetector,
    PackageManagerDetector,
)
from .repository_runtime import (
    BranchManager,
    RepositoryContextManager,
    RepositoryManager,
    RepositoryStateManager,
)
from .models import (
    ArchitectureGraph,
    Dependency,
    Directory,
    File,
    FileIndex,
    ImportGraph,
    Module,
    Package,
    Project,
    ProjectMetadata,
    ProjectSnapshot,
    ProjectStatistics,
    Symbol,
    Workspace,
    WorkspaceMetadata,
    WorkspaceSnapshot,
    WorkspaceStatistics,
)
from .events import WorkspaceEvent, WorkspaceEventType

__all__ = [
    'WorkspaceManager',
    'WorkspaceRegistry',
    'WorkspaceScanner',
    'WorkspaceIndexer',
    'WorkspaceAnalyzer',
    'WorkspaceCache',
    'WorkspaceConfigurationManager',
    'WorkspaceMetadataManager',
    'WorkspaceStatisticsManager',
    'WorkspaceSnapshotManager',
    'ProjectManager',
    'ProjectRegistry',
    'ProjectLoader',
    'ProjectMetadataManager',
    'ProjectConfigurationManager',
    'ProjectSnapshotManager',
    'ProjectContextManager',
    'ProjectStatisticsManager',
    'FileManager',
    'DirectoryManager',
    'FileIndexManager',
    'FileCache',
    'FileMetadataManager',
    'FileWatcher',
    'FileOperationsCoordinator',
    'DependencyGraphManager',
    'ImportGraphManager',
    'SymbolGraphManager',
    'ModuleGraphManager',
    'ArchitectureGraphManager',
    'PackageGraphManager',
    'RepositoryGraphManager',
    'DetectionRegistry',
    'LanguageDetector',
    'PackageManagerDetector',
    'BuildSystemDetector',
    'FrameworkDetector',
    'RepositoryManager',
    'BranchManager',
    'RepositoryContextManager',
    'RepositoryStateManager',
    'WorkspaceContext',
    'WorkspaceEvent',
    'WorkspaceEventType',
    'Workspace',
    'Project',
    'Module',
    'Package',
    'Directory',
    'File',
    'Symbol',
    'Dependency',
    'ImportGraph',
    'ArchitectureGraph',
    'WorkspaceSnapshot',
    'ProjectSnapshot',
    'WorkspaceStatistics',
    'ProjectStatistics',
    'WorkspaceMetadata',
    'ProjectMetadata',
    'WorkspaceManagerInterface',
    'WorkspaceRegistryInterface',
    'WorkspaceScannerInterface',
    'WorkspaceIndexerInterface',
    'ArchitectureAnalyzerInterface',
]
