from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class MemoryType(Enum):
    WORKING = 'working'
    SHORT_TERM = 'short_term'
    CONVERSATION = 'conversation'
    SESSION = 'session'
    AGENT = 'agent'
    SHARED = 'shared'
    PROJECT = 'project'
    KNOWLEDGE = 'knowledge'
    SEMANTIC = 'semantic'
    EPISODIC = 'episodic'
    LONG_TERM = 'long_term'
    CACHE = 'cache'
    TEMPORARY = 'temporary'
    PERSISTENT = 'persistent'
    ARCHIVED = 'archived'


class MemoryState(Enum):
    CREATED = 'created'
    READ = 'read'
    UPDATED = 'updated'
    DELETED = 'deleted'
    ARCHIVED = 'archived'
    RESTORED = 'restored'
    COMPRESSED = 'compressed'
    MERGED = 'merged'
    SPLIT = 'split'
    VERSIONED = 'versioned'
    EXPIRED = 'expired'
    SYNCHRONIZED = 'synchronized'


class MemoryPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class MemoryImportance(Enum):
    TRIVIAL = 'trivial'
    NORMAL = 'normal'
    IMPORTANT = 'important'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class MemoryMetadata:
    namespace: str = ''
    created_by: str = ''
    created_at: str = ''
    updated_at: str = ''
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryReference:
    reference_id: str
    target_id: str
    relationship: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryAction:
    action_id: str
    name: str
    description: str = ''
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    entry_id: str
    type: MemoryType
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: MemoryImportance = MemoryImportance.NORMAL


@dataclass
class MemoryRecord:
    record_id: str
    entries: List[MemoryEntry] = field(default_factory=list)
    namespace: str = ''
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)


@dataclass
class MemoryCollection:
    collection_id: str
    records: List[MemoryRecord] = field(default_factory=list)
    namespace: str = ''
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)


@dataclass
class MemoryNamespace:
    namespace: str
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySnapshot:
    snapshot_id: str
    record: MemoryRecord
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)


@dataclass
class MemoryRelationship:
    source_id: str
    target_id: str
    relation_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryConfiguration:
    default_memory_type: MemoryType = MemoryType.WORKING
    max_entries: int = 1024
    retention_days: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStatistics:
    total_records: int = 0
    total_entries: int = 0
    namespaces: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryContext:
    context_id: str
    memory_type: MemoryType
    namespace: str
    metadata: Dict[str, Any] = field(default_factory=dict)
