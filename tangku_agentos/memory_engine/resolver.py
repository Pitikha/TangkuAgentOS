from __future__ import annotations

from .interfaces import MemoryResolver
from .models import MemoryReference


class MemoryResolverImpl(MemoryResolver):
    """Resolve memory references by returning an in-memory reference object."""

    def __init__(self) -> None:
        self._references: dict[str, MemoryReference] = {}

    def resolve(self, reference_id: str) -> MemoryReference:
        reference = self._references.get(reference_id)
        if reference is None:
            reference = MemoryReference(reference_id=reference_id, target_id=reference_id)
            self._references[reference_id] = reference
        return reference
