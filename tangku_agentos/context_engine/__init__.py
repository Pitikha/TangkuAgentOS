"""Context engine foundation for Tangku AgentOS."""

from .interfaces import (
    ContextBuilderInterface,
    ContextCacheInterface,
    ContextCompressorInterface,
    ContextManagerInterface,
    ContextOptimizerInterface,
    ContextProviderInterface,
    ContextRegistryInterface,
    ContextResolverInterface,
    ContextSnapshotManagerInterface,
)
from .manager import ContextManager
from .builder import ContextBuilder
from .cache import ContextCache
from .compressor import ContextCompressor
from .optimizer import ContextOptimizer
from .provider import ContextProvider
from .registry import ContextRegistry
from .resolver import ContextResolver
from .snapshot import ContextSnapshotManager
from .models import (
    ContextObject,
    ContextSegment,
    ContextSource,
    ContextReference,
    ContextPriority,
    ContextStatistics,
    ContextConfiguration,
    ContextMetadata,
)
from .events import ContextEvent, ContextEventType

__all__ = [
    "ContextObject",
    "ContextSegment",
    "ContextSource",
    "ContextReference",
    "ContextPriority",
    "ContextStatistics",
    "ContextConfiguration",
    "ContextMetadata",
    "ContextManager",
    "ContextBuilder",
    "ContextCache",
    "ContextCompressor",
    "ContextOptimizer",
    "ContextProvider",
    "ContextRegistry",
    "ContextResolver",
    "ContextSnapshotManager",
    "ContextEvent",
    "ContextEventType",
]
