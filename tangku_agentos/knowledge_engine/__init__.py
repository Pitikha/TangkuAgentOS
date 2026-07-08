#!/usr/bin/env python3
"""
TangkuAgentOS Knowledge Engine.

This package provides a production-grade Knowledge Engine for AI agents,
supporting knowledge from multiple sources with advanced retrieval,
semantic search, knowledge graphs, and citation management.

## Features
- Multi-source knowledge support (local files, Git repos, docs, PDFs, web pages, APIs, databases)
- Hybrid search (semantic + keyword + metadata filtering)
- Knowledge graph construction and traversal
- Citation and provenance tracking
- Multi-level caching for performance
- Async indexing and retrieval
- Workspace isolation and permission-aware retrieval

## Usage
```python
from tangku_agentos.knowledge_engine import KnowledgeManager, KnowledgeSource

# Initialize the knowledge manager
knowledge_manager = KnowledgeManager()

# Add a knowledge source
await knowledge_manager.add_source(
    source_type=KnowledgeSource.LOCAL_FILES,
    config={"path": "./documents"},
)

# Index the knowledge
await knowledge_manager.index()

# Search for knowledge
results = await knowledge_manager.search("How do I use TangkuAgentOS?")
for result in results:
    print(f"{result.title}: {result.content[:100]}...")
```
"""

# --- Core Components ---
from .manager import KnowledgeManager
from .provider import (
    KnowledgeProvider,
    BaseKnowledgeProvider,
    FileProvider,
    GitProvider,
    APIProvider,
    DatabaseProvider,
    WebProvider,
    MarkdownProvider,
    PDFProvider,
    DocumentProvider,
)
from .source_manager import KnowledgeSourceManager
from .retrieval import KnowledgeRetrievalManager
from .search import KnowledgeSearchManager
from .semantic import SemanticIndexManager
from .graph_manager import KnowledgeGraphManager
from .citation import CitationManager
from .cache import KnowledgeCache
from .registry import KnowledgeRegistry
from .configuration import KnowledgeConfigurationManager
from .statistics import KnowledgeStatisticsManager

# --- Models and Types ---
from .models import (
    KnowledgeItem,
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeSource,
    KnowledgeSourceType,
    KnowledgeCitation,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeRelationship,
    KnowledgeEntity,
    KnowledgeSession,
    KnowledgeMetadata,
    KnowledgeCollection,
    KnowledgeNamespace,
    KnowledgeSnapshot,
    KnowledgeState,
    KnowledgeConfiguration,
    KnowledgeQuery,
    KnowledgeSearchResult,
    KnowledgeIndexConfig,
    KnowledgeRetrievalConfig,
    KnowledgeGraphConfig,
    KnowledgeCacheConfig,
    KnowledgeCitationConfig,
)

# --- Events ---
from .events import KnowledgeEvent, KnowledgeEventType, KnowledgeEventBus

# --- Exceptions ---
from .exceptions import (
    KnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeExistsError,
    KnowledgeSourceError,
    KnowledgeIndexingError,
    KnowledgeRetrievalError,
    KnowledgeSearchError,
    KnowledgeGraphError,
    KnowledgeCitationError,
    KnowledgeCacheError,
    KnowledgePermissionError,
    KnowledgeValidationError,
    KnowledgeTimeoutError,
)

# --- Interfaces ---
from .interfaces import (
    IKnowledgeManager,
    IKnowledgeProvider,
    IKnowledgeSourceManager,
    IKnowledgeRetrieval,
    IKnowledgeSearch,
    IKnowledgeGraph,
    ICitationManager,
    IKnowledgeCache,
    IKnowledgeRegistry,
    IKnowledgeConfiguration,
    IKnowledgeStatistics,
)

# --- Public API ---
__all__ = [
    # Core Components
    "KnowledgeManager",
    "KnowledgeProvider",
    "BaseKnowledgeProvider",
    "FileProvider",
    "GitProvider",
    "APIProvider",
    "DatabaseProvider",
    "WebProvider",
    "MarkdownProvider",
    "PDFProvider",
    "DocumentProvider",
    "KnowledgeSourceManager",
    "KnowledgeRetrievalManager",
    "KnowledgeSearchManager",
    "SemanticIndexManager",
    "KnowledgeGraphManager",
    "CitationManager",
    "KnowledgeCache",
    "KnowledgeRegistry",
    "KnowledgeConfigurationManager",
    "KnowledgeStatisticsManager",
    # Models and Types
    "KnowledgeItem",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeSource",
    "KnowledgeSourceType",
    "KnowledgeCitation",
    "KnowledgeGraphNode",
    "KnowledgeGraphEdge",
    "KnowledgeRelationship",
    "KnowledgeEntity",
    "KnowledgeSession",
    "KnowledgeMetadata",
    "KnowledgeCollection",
    "KnowledgeNamespace",
    "KnowledgeSnapshot",
    "KnowledgeState",
    "KnowledgeConfiguration",
    "KnowledgeQuery",
    "KnowledgeSearchResult",
    "KnowledgeIndexConfig",
    "KnowledgeRetrievalConfig",
    "KnowledgeGraphConfig",
    "KnowledgeCacheConfig",
    "KnowledgeCitationConfig",
    # Events
    "KnowledgeEvent",
    "KnowledgeEventType",
    "KnowledgeEventBus",
    # Exceptions
    "KnowledgeError",
    "KnowledgeNotFoundError",
    "KnowledgeExistsError",
    "KnowledgeSourceError",
    "KnowledgeIndexingError",
    "KnowledgeRetrievalError",
    "KnowledgeSearchError",
    "KnowledgeGraphError",
    "KnowledgeCitationError",
    "KnowledgeCacheError",
    "KnowledgePermissionError",
    "KnowledgeValidationError",
    "KnowledgeTimeoutError",
    # Interfaces
    "IKnowledgeManager",
    "IKnowledgeProvider",
    "IKnowledgeSourceManager",
    "IKnowledgeRetrieval",
    "IKnowledgeSearch",
    "IKnowledgeGraph",
    "ICitationManager",
    "IKnowledgeCache",
    "IKnowledgeRegistry",
    "IKnowledgeConfiguration",
    "IKnowledgeStatistics",
]
