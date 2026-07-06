from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class MemoryEventType(Enum):
    CREATED = 'memory.created'
    READ = 'memory.read'
    UPDATED = 'memory.updated'
    DELETED = 'memory.deleted'
    ARCHIVED = 'memory.archived'
    RESTORED = 'memory.restored'
    COMPRESSED = 'memory.compressed'
    SYNCHRONIZED = 'memory.synchronized'


class MemoryEventPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class MemoryEvent:
    event_type: MemoryEventType
    memory_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MemoryEventPriority = MemoryEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
