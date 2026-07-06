from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class KnowledgeState(Enum):
    AVAILABLE = 'available'
    ARCHIVED = 'archived'
    OBSOLETE = 'obsolete'
    ERROR = 'error'


class KnowledgeSourceType(Enum):
    DOCUMENTATION = 'documentation'
    CODE = 'code'
    MARKDOWN = 'markdown'
    PDF = 'pdf'
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    WEBSITE = 'website'
    API = 'api'
    DATABASE = 'database'
    OFFICE = 'office'
    NOTES = 'notes'
    RESEARCH = 'research'


class SearchType(Enum):
    SEMANTIC = 'semantic'
    KEYWORD = 'keyword'
    HYBRID = 'hybrid'
    GRAPH = 'graph'
    METADATA = 'metadata'


@dataclass(frozen=True)
class KnowledgeMetadata:
    title: str = ''
    source_type: KnowledgeSourceType = KnowledgeSourceType.TEXT
    authors: List[str] = field(default_factory=list)
    created_at: str = ''
    updated_at: str = ''
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeSource:
    source_id: str
    source_type: KnowledgeSourceType
    uri: str = ''
    metadata: KnowledgeMetadata = field(default_factory=lambda: KnowledgeMetadata(title='', source_type=KnowledgeSourceType.TEXT))


@dataclass(frozen=True)
class KnowledgeItem:
    item_id: str
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: KnowledgeMetadata = field(default_factory=lambda: KnowledgeMetadata(title='', source_type=KnowledgeSourceType.TEXT))


@dataclass(frozen=True)
class KnowledgeDocument(KnowledgeItem):
    document_id: str = ''
    source: KnowledgeSource = field(default_factory=lambda: KnowledgeSource(source_id='', source_type=KnowledgeSourceType.TEXT))


@dataclass(frozen=True)
class KnowledgeChunk(KnowledgeItem):
    chunk_id: str = ''
    document_id: str = ''
    source: KnowledgeSource = field(default_factory=lambda: KnowledgeSource(source_id='', source_type=KnowledgeSourceType.TEXT))


@dataclass(frozen=True)
class KnowledgeCitation:
    citation_id: str
    item_id: str
    source_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeGraphNode:
    node_id: str
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeGraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEntity:
    entity_id: str
    name: str
    description: str = ''
    entity_type: str = 'entity'
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = ''
    updated_at: str = ''
    version: int = 1
    confidence_score: float = 1.0
    source_references: List[str] = field(default_factory=list)

    @property
    def item_id(self) -> str:
        return self.entity_id


@dataclass
class KnowledgeRelationship:
    relationship_id: str = ''
    source_entity_id: str = ''
    target_entity_id: str = ''
    relationship_type: str = 'related_to'
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: str = ''
    subject_id: str = ''
    object_id: str = ''
    relation: str = ''

    def __post_init__(self) -> None:
        if not self.relationship_id:
            self.relationship_id = f"{self.source_entity_id or self.subject_id}->{self.target_entity_id or self.object_id}:{self.relationship_type or self.relation}"  # type: ignore[arg-type]
        if not self.source_entity_id and self.subject_id:
            self.source_entity_id = self.subject_id
        if not self.target_entity_id and self.object_id:
            self.target_entity_id = self.object_id
        if not self.relationship_type and self.relation:
            self.relationship_type = self.relation


@dataclass
class KnowledgeCollection:
    collection_id: str
    documents: List[Any] = field(default_factory=list)
    metadata: KnowledgeMetadata = field(default_factory=lambda: KnowledgeMetadata(title='', source_type=KnowledgeSourceType.TEXT))


@dataclass
class KnowledgeNamespace:
    namespace: str
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSnapshot:
    snapshot_id: str
    collection: KnowledgeCollection
    metadata: KnowledgeMetadata = field(default_factory=lambda: KnowledgeMetadata(title='', source_type=KnowledgeSourceType.TEXT))


@dataclass
class KnowledgeConfiguration:
    search_types: List[SearchType | str] = field(default_factory=lambda: [SearchType.SEMANTIC])
    enable_citation_tracking: bool = True
    cache_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSession:
    session_id: str
    state: str = 'active'
    metadata: Dict[str, Any] = field(default_factory=dict)
