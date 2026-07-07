"""Capability layer foundation for Tangku AgentOS."""

from .interfaces import (
    CapabilityDispatcher,
    CapabilityManagerInterface,
    CapabilityRegistryInterface,
    CapabilityResolver,
    CapabilityRequestHandler,
    CapabilityResponseProvider,
)
from .manager import CapabilityManager
from .registry import CapabilityRegistry
from .resolver import CapabilityResolverImpl
from .dispatcher import CapabilityDispatcherImpl
from .models import (
    CapabilityCategory,
    CapabilityContext,
    CapabilityMetadata,
    CapabilityPermission,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityResult,
    CapabilityState,
    CapabilityConfiguration,
)
from .events import CapabilityEvent, CapabilityEventType, CapabilityEventManagerImpl

__all__ = [
    "CapabilityCategory",
    "CapabilityContext",
    "CapabilityMetadata",
    "CapabilityPermission",
    "CapabilityRequest",
    "CapabilityResponse",
    "CapabilityResult",
    "CapabilityState",
    "CapabilityConfiguration",
    "CapabilityManager",
    "CapabilityRegistry",
    "CapabilityResolverImpl",
    "CapabilityDispatcherImpl",
    "CapabilityEvent",
    "CapabilityEventType",
    "CapabilityEventManagerImpl",
    "CapabilityManagerInterface",
    "CapabilityRegistryInterface",
    "CapabilityResolver",
    "CapabilityDispatcher",
    "CapabilityRequestHandler",
    "CapabilityResponseProvider",
]