"""
Message Infrastructure Package Initialization

Exports core message bus components for system-wide usage.
"""

from tangku_agentos.message_infrastructure.bus import (
    MessageBus,
    Message,
    MessagePriority,
    MessageStatus,
    MessageHandler,
    SyncMessageHandler,
    MessageSubscription,
    MessageFilter,
    RoutingRule,
)

from tangku_agentos.message_infrastructure.events import (
    SystemEvent,
    EventType,
    ProgressEvent,
)

from tangku_agentos.message_infrastructure.routing import (
    Router,
    Route,
    ContentBasedRouter,
)

from tangku_agentos.message_infrastructure.storage import (
    MessageStore,
    StorageBackend,
)

from tangku_agentos.message_infrastructure.correlation import (
    CorrelationManager,
    Trace,
)

from tangku_agentos.message_infrastructure.monitoring import (
    MessageInfrastructureMonitor,
    MessageMetric,
    HandlerMetric,
    RoutingMetric,
)

__all__ = [
    # Bus
    "MessageBus",
    "Message",
    "MessagePriority",
    "MessageStatus",
    "MessageHandler",
    "SyncMessageHandler",
    "MessageSubscription",
    "MessageFilter",
    "RoutingRule",
    # Events
    "SystemEvent",
    "EventType",
    "ProgressEvent",
    # Routing
    "Router",
    "Route",
    "ContentBasedRouter",
    # Storage
    "MessageStore",
    "StorageBackend",
    # Correlation
    "CorrelationManager",
    "Trace",
    # Monitoring
    "MessageInfrastructureMonitor",
    "MessageMetric",
    "HandlerMetric",
    "RoutingMetric",
]
