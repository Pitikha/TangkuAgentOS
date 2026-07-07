"""Project intelligence architecture for Tangku AgentOS."""

from .interfaces import (
    ArchitectureAnalyzer,
    BuildAnalyzer,
    ConfigurationAnalyzer,
    DependencyAnalyzer,
    FrameworkAnalyzer,
    PackageAnalyzer,
    ProjectAnalyzer,
    ProjectGraph,
    ProjectIntelligenceManager,
    ProjectRegistryInterface,
    ProjectSession,
    ServiceGraph,
    ModuleGraph,
    ComponentGraph,
    DependencyTree,
    TestStructureAnalyzer,
    DocumentationAnalyzer,
)
from .manager import ProjectIntelligenceManager
from .registry import ProjectRegistry
from .models import (
    ComponentGraph,
    DependencyTree,
    ModuleGraph,
    ProjectGraph,
    Repository,
    ServiceGraph,
)

__all__ = [
    "ProjectIntelligenceManager",
    "ProjectRegistry",
    "ProjectRegistryInterface",
    "ProjectAnalyzer",
    "DependencyAnalyzer",
    "ArchitectureAnalyzer",
    "BuildAnalyzer",
    "FrameworkAnalyzer",
    "PackageAnalyzer",
    "TestStructureAnalyzer",
    "DocumentationAnalyzer",
    "ConfigurationAnalyzer",
    "ProjectGraph",
    "ModuleGraph",
    "DependencyTree",
    "ServiceGraph",
    "ComponentGraph",
    "Repository",
    "ProjectSession",
]
