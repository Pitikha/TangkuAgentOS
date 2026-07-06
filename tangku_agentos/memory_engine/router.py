from __future__ import annotations

from .interfaces import MemoryRouter
from .models import MemoryEntry, MemoryType


class MemoryRouterImpl(MemoryRouter):
    """Route entries to appropriate namespaces based on memory type."""

    def route(self, entry: MemoryEntry) -> str:
        type_to_namespace = {
            MemoryType.WORKING: 'working',
            MemoryType.SESSION: 'session',
            MemoryType.CONVERSATION: 'conversation',
            MemoryType.AGENT: 'agent',
            MemoryType.SHARED: 'shared',
            MemoryType.PROJECT: 'project',
            MemoryType.LONG_TERM: 'long_term',
            MemoryType.SEMANTIC: 'semantic',
            MemoryType.EPISODIC: 'episodic',
            MemoryType.PERSISTENT: 'persistent',
            MemoryType.ARCHIVED: 'archive',
        }
        return type_to_namespace.get(entry.type, 'default')
