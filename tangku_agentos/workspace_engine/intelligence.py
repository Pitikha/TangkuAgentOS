from __future__ import annotations

from .models import ArchitectureGraph, Dependency, File, Module, ImportGraph


class DependencyGraphManager:
    """Manage dependency edges between files and modules."""

    def __init__(self) -> None:
        self._dependencies: list[Dependency] = []

    def add_dependency(self, source: str, target: str, metadata: dict[str, object] | None = None) -> None:
        self._dependencies.append(Dependency(source=source, target=target, metadata=metadata or {}))

    def list_dependencies(self) -> list[Dependency]:
        return list(self._dependencies)


class ImportGraphManager:
    """Manage import graphs for files."""

    def __init__(self) -> None:
        self._graph = ImportGraph(graph_id='import-graph')

    def add_edge(self, source: File, target: File) -> None:
        self._graph.edges.append(Dependency(source=source.path, target=target.path, metadata={}))
        if source not in self._graph.nodes:
            self._graph.nodes.append(source)
        if target not in self._graph.nodes:
            self._graph.nodes.append(target)

    def graph(self) -> ImportGraph:
        return self._graph


class SymbolGraphManager:
    """Store symbol-level graph metadata."""

    def __init__(self) -> None:
        self._nodes: list[Module] = []

    def add_module(self, module: Module) -> None:
        self._nodes.append(module)

    def list_modules(self) -> list[Module]:
        return list(self._nodes)


class ModuleGraphManager:
    """Track module relationships."""

    def __init__(self) -> None:
        self._graph = ArchitectureGraph(graph_id='module-graph')

    def add_module(self, module: Module) -> None:
        self._graph.nodes.append(module)

    def graph(self) -> ArchitectureGraph:
        return self._graph


class ArchitectureGraphManager:
    """Store architecture graph nodes and edges."""

    def __init__(self) -> None:
        self._graph = ArchitectureGraph(graph_id='architecture-graph')

    def add_module(self, module: Module) -> None:
        self._graph.nodes.append(module)

    def add_edge(self, source: Module, target: Module) -> None:
        self._graph.edges.append(Dependency(source=source.module_id, target=target.module_id, metadata={}))

    def graph(self) -> ArchitectureGraph:
        return self._graph


class PackageGraphManager:
    """Track package-level graph entries."""

    def __init__(self) -> None:
        self._dependencies: list[Dependency] = []

    def add_dependency(self, source: str, target: str) -> None:
        self._dependencies.append(Dependency(source=source, target=target, metadata={}))

    def list_dependencies(self) -> list[Dependency]:
        return list(self._dependencies)


class RepositoryGraphManager:
    """Track repository graph structure as a collection of dependencies."""

    def __init__(self) -> None:
        self._dependencies: list[Dependency] = []

    def add_dependency(self, source: str, target: str) -> None:
        self._dependencies.append(Dependency(source=source, target=target, metadata={}))

    def list_dependencies(self) -> list[Dependency]:
        return list(self._dependencies)
