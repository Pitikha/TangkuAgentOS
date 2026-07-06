from __future__ import annotations

from typing import Dict, Optional

from .interfaces import KnowledgeCacheInterface
from .models import KnowledgeDocument


class KnowledgeCache(KnowledgeCacheInterface):
    """Skeleton knowledge cache."""

    def __init__(self) -> None:
        self._cache: Dict[str, KnowledgeDocument] = {}

    def get(self, key: str) -> KnowledgeDocument | None:
        return self._cache.get(key)

    def put(self, document: KnowledgeDocument) -> None:
        self._cache[document.document_id] = document
