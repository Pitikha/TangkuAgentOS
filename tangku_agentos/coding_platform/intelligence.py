from __future__ import annotations

from threading import RLock
from typing import Any


class CodeIndexManager:
    _shared_indices: dict[str, dict[str, Any]] = {}

    def __init__(self) -> None:
        self._indices: dict[str, dict[str, Any]] = self.__class__._shared_indices
        self._lock = RLock()

    def index_project(self, project_id: str, *, files: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            payload = {"files": len(files or []), "metadata": metadata or {}}
            self._indices[project_id] = payload
            return payload

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._indices)


class CodeGraphManager:
    _shared_dependencies: list[tuple[str, str]] = []

    def __init__(self) -> None:
        self._dependencies: list[tuple[str, str]] = self.__class__._shared_dependencies
        self._lock = RLock()

    def add_dependency(self, source: str, target: str) -> None:
        with self._lock:
            self._dependencies.append((source, target))

    def snapshot(self) -> dict[str, list[tuple[str, str]]]:
        with self._lock:
            return {"dependencies": list(self._dependencies)}


class SymbolManager:
    _shared_symbols: dict[str, dict[str, Any]] = {}

    def __init__(self) -> None:
        self._symbols: dict[str, dict[str, Any]] = self.__class__._shared_symbols
        self._lock = RLock()

    def register_symbol(self, symbol_id: str, qualified_name: str, *, kind: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            payload = {"qualified_name": qualified_name, "kind": kind, "metadata": metadata or {}}
            self._symbols[qualified_name] = payload
            return payload

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._symbols)


class StaticAnalysisManager:
    _shared_analyses: dict[str, dict[str, Any]] = {}

    def __init__(self) -> None:
        self._analyses: dict[str, dict[str, Any]] = self.__class__._shared_analyses
        self._lock = RLock()

    def add_analysis(self, project_id: str, analysis: dict[str, Any]) -> None:
        with self._lock:
            self._analyses[project_id] = analysis

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._analyses)


class SearchManager:
    _shared_terms: list[str] = []

    def __init__(self) -> None:
        self._terms: list[str] = self.__class__._shared_terms
        self._lock = RLock()

    def index_search_term(self, term: str) -> None:
        with self._lock:
            self._terms.append(term)

    def snapshot(self) -> list[str]:
        with self._lock:
            return list(self._terms)


class CodeIntelligenceManager:
    def __init__(self) -> None:
        self.index_manager = CodeIndexManager()
        self.symbol_manager = SymbolManager()
        self.graph_manager = CodeGraphManager()
        self.analysis_manager = StaticAnalysisManager()
        self.search_manager = SearchManager()

    def snapshot(self) -> dict[str, Any]:
        return {
            "indices": self.index_manager.snapshot(),
            "symbols": self.symbol_manager.snapshot(),
            "graph": self.graph_manager.snapshot(),
            "analysis": self.analysis_manager.snapshot(),
            "search": self.search_manager.snapshot(),
        }

    def register_index(self, project_id: str, *, files: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.index_manager.index_project(project_id, files=files, metadata=metadata)

    def register_symbol(self, symbol_id: str, qualified_name: str, *, kind: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.symbol_manager.register_symbol(symbol_id, qualified_name, kind=kind, metadata=metadata)

    def add_dependency(self, source: str, target: str) -> None:
        self.graph_manager.add_dependency(source, target)

    def add_analysis(self, project_id: str, analysis: dict[str, Any]) -> None:
        self.analysis_manager.add_analysis(project_id, analysis)

    def index_search_term(self, term: str) -> None:
        self.search_manager.index_search_term(term)
