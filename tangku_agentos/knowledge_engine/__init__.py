"""Knowledge engine foundation for Tangku AgentOS."""

from .interfaces import (
    CitationManagerInterface,
    GraphManagerInterface,
    KnowledgeManagerInterface,
    KnowledgeProvider,
    KnowledgeRegistryInterface,
    KnowledgeSearchManagerInterface,
    KnowledgeSourceManagerInterface,
    KnowledgeStatisticsManagerInterface,
    KnowledgeConfigurationManagerInterface,
    KnowledgeCacheInterface,
    KnowledgeResolverInterface,
    KnowledgeEventManagerInterface,
)
from .manager import KnowledgeManager
from .registry import KnowledgeRegistry
from .provider import KnowledgeProviderImpl
from .source_manager import KnowledgeSourceManager
from .graph_manager import KnowledgeGraphManager
from .retrieval import KnowledgeRetrievalManager
from .search import KnowledgeSearchManager
from .citation import CitationManager
from .cache import KnowledgeCache
from .statistics import KnowledgeStatisticsManager
from .configuration import KnowledgeConfigurationManager
from .events import KnowledgeEvent, KnowledgeEventType
from .semantic import (
    CitationManager,
    ContextAssemblyManager,
    DocumentManager,
    KnowledgeSyncManager,
    RetrievalManager,
    SemanticIndexManager,
)
from .models import (
    KnowledgeChunk,
    KnowledgeCitation,
    KnowledgeCollection,
    KnowledgeConfiguration,
    KnowledgeDocument,
    KnowledgeEntity,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeItem,
    KnowledgeMetadata,
    KnowledgeNamespace,
    KnowledgeRelationship,
    KnowledgeSession,
    KnowledgeSnapshot,
    KnowledgeSource,
    KnowledgeSourceType,
    KnowledgeState,
)

__all__ = [
    'KnowledgeManager',
    'KnowledgeRegistry',
    'KnowledgeProviderImpl',
    'KnowledgeSourceManager',
    'KnowledgeGraphManager',
    'KnowledgeRetrievalManager',
    'KnowledgeSearchManager',
    'CitationManager',
    'ContextAssemblyManager',
    'DocumentManager',
    'KnowledgeSyncManager',
    'RetrievalManager',
    'SemanticIndexManager',
    'KnowledgeCache',
    'KnowledgeStatisticsManager',
    'KnowledgeConfigurationManager',
    'KnowledgeEvent',
    'KnowledgeEventType',
    'KnowledgeItem',
    'KnowledgeDocument',
    'KnowledgeChunk',
    'KnowledgeSource',
    'KnowledgeCitation',
    'KnowledgeGraphNode',
    'KnowledgeGraphEdge',
    'KnowledgeRelationship',
    'KnowledgeEntity',
    'KnowledgeSession',
    'KnowledgeMetadata',
    'KnowledgeCollection',
    'KnowledgeNamespace',
    'KnowledgeSnapshot',
    'KnowledgeSourceType',
    'KnowledgeState',
    'KnowledgeConfiguration',
    'KnowledgeManagerInterface',
    'KnowledgeRegistryInterface',
    'KnowledgeSourceManagerInterface',
    'GraphManagerInterface',
    'KnowledgeSearchManagerInterface',
    'CitationManagerInterface',
]
