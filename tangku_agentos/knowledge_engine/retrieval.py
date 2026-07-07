from __future__ import annotations

from .interfaces import KnowledgeRetrievalManagerInterface
from .models import KnowledgeCollection, KnowledgeDocument


class KnowledgeRetrievalManager(KnowledgeRetrievalManagerInterface):
    """Provide a placeholder retrieval collection based on the query string."""

    def __init__(self) -> None:
        self._documents: list[KnowledgeDocument] = []

    def retrieve(self, query: str) -> KnowledgeCollection:
        if not query:
            return KnowledgeCollection(collection_id='retrieval', documents=[])
        return KnowledgeCollection(collection_id='retrieval', documents=list(self._documents))

    def register_document(self, document: KnowledgeDocument) -> None:
        self._documents.append(document)
