from __future__ import annotations

from typing import Dict, List

from .exceptions import KnowledgeSourceError
from .interfaces import KnowledgeSourceManagerInterface
from .models import KnowledgeSource


class KnowledgeSourceManager(KnowledgeSourceManagerInterface):
    """Skeleton knowledge source manager."""

    def __init__(self) -> None:
        self._sources: Dict[str, KnowledgeSource] = {}

    def register_source(self, source: KnowledgeSource) -> None:
        self._sources[source.source_id] = source

    def get_source(self, source_id: str) -> KnowledgeSource:
        source = self._sources.get(source_id)
        if source is None:
            raise KnowledgeSourceError(f'Source not found: {source_id}')
        return source

    def list_sources(self) -> list[KnowledgeSource]:
        return list(self._sources.values())
