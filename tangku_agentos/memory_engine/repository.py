from __future__ import annotations

from .interfaces import MemoryRepository
from .models import MemoryCollection


class MemoryRepositoryImpl(MemoryRepository):
    """Repository abstraction for retrieving and persisting collections."""

    def __init__(self) -> None:
        self._collections: dict[str, MemoryCollection] = {}

    def retrieve_collection(self, namespace: str) -> MemoryCollection:
        collection = self._collections.get(namespace)
        if collection is None:
            collection = MemoryCollection(collection_id=namespace, namespace=namespace)
            self._collections[namespace] = collection
        return collection

    def persist_collection(self, collection: MemoryCollection) -> None:
        self._collections[collection.namespace or collection.collection_id] = collection
