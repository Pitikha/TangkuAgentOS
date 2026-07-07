from __future__ import annotations

from .interfaces import KnowledgeSearchManagerInterface
from .models import KnowledgeCollection, KnowledgeDocument, KnowledgeEntity


class KnowledgeSearchManager(KnowledgeSearchManagerInterface):
    """Search registered knowledge entities by text and metadata."""

    def __init__(self) -> None:
        self._documents: list[KnowledgeDocument | KnowledgeEntity] = []

    def search(self, query: str, **_: object) -> KnowledgeCollection:
        normalized = query.lower()
        matches = [
            document
            for document in self._documents
            if normalized in str(getattr(document, "name", "")).lower()
            or normalized in str(getattr(document, "entity_type", "")).lower()
            or normalized in str(getattr(document, "description", "")).lower()
            or normalized in str(getattr(document, "metadata", {})).lower()
        ]
        return KnowledgeCollection(collection_id='search', documents=list(matches))

    def lookup_by_id(self, item_id: str) -> list[KnowledgeDocument | KnowledgeEntity]:
        return [document for document in self._documents if getattr(document, "item_id", None) == item_id or getattr(document, "entity_id", None) == item_id]

    def lookup_by_name(self, name: str) -> list[KnowledgeDocument | KnowledgeEntity]:
        normalized = name.lower()
        return [document for document in self._documents if normalized in str(getattr(document, "name", "")).lower()]

    def lookup_by_tag(self, tag: str) -> list[KnowledgeDocument | KnowledgeEntity]:
        normalized = tag.lower()
        return [document for document in self._documents if any(normalized == str(item).lower() for item in getattr(document, "tags", []))]

    def lookup_by_type(self, entity_type: str) -> list[KnowledgeDocument | KnowledgeEntity]:
        normalized = entity_type.lower()
        return [document for document in self._documents if normalized == str(getattr(document, "entity_type", "")).lower()]

    def lookup_by_metadata(self, key: str, value: object) -> list[KnowledgeDocument | KnowledgeEntity]:
        return [document for document in self._documents if document.metadata.get(key) == value] if hasattr(next(iter(self._documents), None), "metadata") else []

    def register_document(self, document: KnowledgeDocument | KnowledgeEntity) -> None:
        self._documents.append(document)
