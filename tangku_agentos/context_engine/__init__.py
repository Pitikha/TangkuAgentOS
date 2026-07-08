#!/usr/bin/env python3
"""
TangkuAgentOS Context Engine.

This package provides a production-grade Context Management System for AI agents,
supporting context assembly, optimization, compression, budgeting, caching, and session management.

## Features
- Multi-source context assembly from Memory Engine, Knowledge Engine, and other sources
- Context optimization with token budgeting, semantic compression, and hierarchical summarization
- Context caching with multi-level cache, invalidation, and incremental updates
- Session management with multi-session support, shared workspaces, and snapshots
- Security features including context isolation, permission-aware filtering, and sensitive data masking

## Usage
```python
from tangku_agentos.context_engine import ContextManager, ContextAssembler, ContextOptimizer

# Initialize the context manager
context_manager = ContextManager()

# Create a context assembler
assembler = ContextAssembler()

# Assemble context from multiple sources
context = await assembler.assemble([
    {"source": "memory", "query": "recent conversation"},
    {"source": "knowledge", "query": "relevant documents"},
])

# Optimize the context
optimized_context = await context_manager.optimize(context, token_budget=4096)

# Get the final context string
context_string = optimized_context.to_string()
```
"""

# --- Core Components ---
from .manager import ContextManager
from .assembler import ContextAssembler, MultiSourceAssembler, PriorityAssembler, MergeAssembler
from .builder import ContextBuilder, MetadataEnricher
from .optimizer import ContextOptimizer, TokenBudget, SemanticCompressor, HierarchicalSummarizer
from .compressor import ContextCompressor, BaseContextCompressor
from .budget import ContextBudget, TokenBudgetManager, BaseTokenBudget
from .cache import ContextCache, MultiLevelCache, CacheInvalidator, BaseContextCache
from .session import ContextSession, SessionManager, WorkspaceManager, BaseContextSession
from .provider import ContextProvider, MultiSourceProvider, SourceAttributor, BaseContextProvider
from .registry import ContextRegistry, BaseContextRegistry
from .resolver import ContextResolver, DependencyResolver, BaseContextResolver

# --- Models and Types ---
from .models import (
    Context,
    ContextType,
    ContextMetadata,
    ContextSource,
    ContextChunk,
    ContextAssemblyResult,
    ContextOptimizationResult,
    ContextCompressionResult,
    ContextBudgetResult,
    ContextCacheResult,
    ContextSessionResult,
    ContextConfig,
    AssemblyConfig,
    OptimizationConfig,
    CompressionConfig,
    BudgetConfig,
    CacheConfig,
    SessionConfig,
)

# --- Events ---
from .events import ContextEvent, ContextEventType, ContextEventBus

# --- Configuration ---
from .configuration import ContextConfigManager, BaseContextConfig

# --- Exceptions ---
from .exceptions import (
    ContextError,
    ContextNotFoundError,
    ContextExistsError,
    ContextAssemblyError,
    ContextOptimizationError,
    ContextCompressionError,
    ContextBudgetError,
    ContextCacheError,
    ContextSessionError,
    ContextPermissionError,
    ContextValidationError,
    ContextTimeoutError,
)

# --- Interfaces ---
from .interfaces import (
    IContextManager,
    IContextAssembler,
    IContextBuilder,
    IContextOptimizer,
    IContextCompressor,
    IContextBudget,
    IContextCache,
    IContextSession,
    IContextProvider,
    IContextRegistry,
    IContextResolver,
)

# --- Utilities ---
from .snapshot import ContextSnapshot, ContextSnapshotManager
from .optimizer import ContextRanker, RelevanceScorer

# --- Public API ---
__all__ = [
    # Core Components
    "ContextManager",
    "ContextAssembler",
    "MultiSourceAssembler",
    "PriorityAssembler",
    "MergeAssembler",
    "ContextBuilder",
    "MetadataEnricher",
    "ContextOptimizer",
    "TokenBudget",
    "SemanticCompressor",
    "HierarchicalSummarizer",
    "ContextCompressor",
    "BaseContextCompressor",
    "ContextBudget",
    "TokenBudgetManager",
    "BaseTokenBudget",
    "ContextCache",
    "MultiLevelCache",
    "CacheInvalidator",
    "BaseContextCache",
    "ContextSession",
    "SessionManager",
    "WorkspaceManager",
    "BaseContextSession",
    "ContextProvider",
    "MultiSourceProvider",
    "SourceAttributor",
    "BaseContextProvider",
    "ContextRegistry",
    "BaseContextRegistry",
    "ContextResolver",
    "DependencyResolver",
    "BaseContextResolver",
    # Models and Types
    "Context",
    "ContextType",
    "ContextMetadata",
    "ContextSource",
    "ContextChunk",
    "ContextAssemblyResult",
    "ContextOptimizationResult",
    "ContextCompressionResult",
    "ContextBudgetResult",
    "ContextCacheResult",
    "ContextSessionResult",
    "ContextConfig",
    "AssemblyConfig",
    "OptimizationConfig",
    "CompressionConfig",
    "BudgetConfig",
    "CacheConfig",
    "SessionConfig",
    # Events
    "ContextEvent",
    "ContextEventType",
    "ContextEventBus",
    # Configuration
    "ContextConfigManager",
    "BaseContextConfig",
    # Exceptions
    "ContextError",
    "ContextNotFoundError",
    "ContextExistsError",
    "ContextAssemblyError",
    "ContextOptimizationError",
    "ContextCompressionError",
    "ContextBudgetError",
    "ContextCacheError",
    "ContextSessionError",
    "ContextPermissionError",
    "ContextValidationError",
    "ContextTimeoutError",
    # Interfaces
    "IContextManager",
    "IContextAssembler",
    "IContextBuilder",
    "IContextOptimizer",
    "IContextCompressor",
    "IContextBudget",
    "IContextCache",
    "IContextSession",
    "IContextProvider",
    "IContextRegistry",
    "IContextResolver",
    # Utilities
    "ContextSnapshot",
    "ContextSnapshotManager",
    "ContextRanker",
    "RelevanceScorer",
]
