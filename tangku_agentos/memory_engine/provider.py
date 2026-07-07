from __future__ import annotations

from .interfaces import MemoryProvider
from .models import MemoryCollection


class MemoryProviderImpl(MemoryProvider):
    """Provide memory collections by namespace through an in-memory store."""

    def __init__(self) -> None:
        self._collections: dict[str, MemoryCollection] = {}

    def load(self, namespace: str) -> MemoryCollection:
        collection = self._collections.get(namespace)
        if collection is None:
            collection = MemoryCollection(collection_id=namespace, namespace=namespace)
            self._collections[namespace] = collection
        return collection

    def persist(self, collection: MemoryCollection) -> None:
        self._collections[collection.namespace or collection.collection_id] = collection
