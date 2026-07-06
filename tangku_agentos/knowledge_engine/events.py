from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class KnowledgeEventType(Enum):
    INGESTED = 'knowledge.ingested'
    INDEXED = 'knowledge.indexed'
    RETRIEVED = 'knowledge.retrieved'
    SEARCHED = 'knowledge.searched'
    CITED = 'knowledge.cited'
    ARCHIVED = 'knowledge.archived'


class KnowledgeEventPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class KnowledgeEvent:
    event_type: KnowledgeEventType
    item_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: KnowledgeEventPriority = KnowledgeEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
