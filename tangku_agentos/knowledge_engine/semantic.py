from __future__ import annotations

from threading import RLock
from typing import Any


class SemanticIndexManager:
    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def index_document(self, document_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._documents[document_id] = {"metadata": metadata}

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._documents)


class RetrievalManager:
    def __init__(self) -> None:
        self._sources: list[tuple[str, dict[str, Any]]] = []
        self._lock = RLock()

    def add_source(self, source_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._sources.append((source_id, metadata))

    def snapshot(self) -> dict[str, list[tuple[str, dict[str, Any]]]]:
        with self._lock:
            return {"sources": list(self._sources)}


class DocumentManager:
    def __init__(self) -> None:
        self._documents: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def register_document(self, document_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._documents[document_id] = {"metadata": metadata}

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._documents)


class ContextAssemblyManager:
    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def add_context(self, context_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._contexts[context_id] = metadata

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._contexts)


class CitationManager:
    def __init__(self) -> None:
        self._citations: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def add_citation(self, document_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._citations[document_id] = metadata

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._citations)


class KnowledgeSyncManager:
    def __init__(self) -> None:
        self._syncs: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def sync(self, target_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._syncs[target_id] = metadata

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._syncs)
