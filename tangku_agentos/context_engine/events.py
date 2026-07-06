from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class ContextEventType(Enum):
    CREATED = "context.created"
    UPDATED = "context.updated"
    DELETED = "context.deleted"
    SNAPSHOT_CREATED = "context.snapshot_created"
    RESOLVED = "context.resolved"
    COMPRESSED = "context.compressed"
    OPTIMIZED = "context.optimized"
    CACHE_HIT = "context.cache_hit"
    CACHE_MISS = "context.cache_miss"


class ContextEventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ContextEvent:
    event_type: ContextEventType
    context_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: ContextEventPriority = ContextEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
