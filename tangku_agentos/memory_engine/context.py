from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .models import MemoryContext, MemoryType


@dataclass
class MemoryContextObject(MemoryContext):
    state: Dict[str, Any] = field(default_factory=dict)


class MemoryContextManager:
    """Skeleton memory context manager."""

    def build_context(self, memory_type: MemoryType, namespace: str) -> MemoryContextObject:
        return MemoryContextObject(context_id=f'{namespace}-{memory_type.value}', memory_type=memory_type, namespace=namespace)
