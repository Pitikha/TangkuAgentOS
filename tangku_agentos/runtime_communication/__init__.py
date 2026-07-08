"""
TangkuAgentOS Runtime Communication Framework

A unified communication layer that allows every runtime inside TangkuAgentOS
to communicate safely, efficiently, and asynchronously.

This framework provides:
- Message Bus for direct and broadcast communication
- Event Bus for publish/subscribe patterns
- Command Bus for command execution
- Query Bus for request/response patterns
- Broadcast Bus for one-to-many communication
- Request/Response Bus for request/reply patterns
- Protocols for different communication patterns (PubSub, Request/Reply, Stream, AsyncTask)
- Runtime Services for discovery, registry, health, metadata, context, and session management
- Complete message models with validation and serialization support
- Comprehensive exception hierarchy

Phase 1 Implementation (Core Message Infrastructure):
- All message models (Message, Event, Command, Query, Response, Broadcast, Notification, StreamMessage, AsyncTask, ScheduledTask)
- All message buses (MessageBus, EventBus, CommandBus, QueryBus, BroadcastBus, RequestResponseBus)
- All communication protocols (PubSubProtocol, RequestReplyProtocol, StreamProtocol, AsyncTaskProtocol)
- All runtime services (RuntimeDiscoveryService, RuntimeRegistry, RuntimeHealthService, RuntimeStatusManager, RuntimeMetadataRegistry, RuntimeContextManager, RuntimeSessionManager)
- Complete exception hierarchy
- Full type hints and documentation

Example usage:
    from tangku_agentos.runtime_communication import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
        RuntimeRegistry,
        RuntimeDiscoveryService,
    )
"""

# =============================================================================
# CORE MODELS
# =============================================================================

from tangku_agentos.runtime_communication.models.messages import (
    Message,
    MessageType,
    MessagePriority,
    MessageStatus,
    Event,
    Command,
    Query,
    Response,
    Broadcast,
    Notification,
    StreamMessage,
    AsyncTask,
    ScheduledTask,
    MessageEnvelope,
)

from tangku_agentos.runtime_communication.models.exceptions import (
    MessageError,
    MessageDeliveryError,
    MessageTimeoutError,
    MessageValidationError,
    AuthorizationError,
    CircuitBreakerOpenError,
    DuplicateMessageError,
    RuntimeNotFoundError,
    RuntimeNotAvailableError,
    RuntimeCommunicationError,
    SerializationError,
    DeserializationError,
)

# =============================================================================
# BUSES
# =============================================================================

from tangku_agentos.runtime_communication.buses.message_bus import (
    MessageBus,
    Subscription,
    RoutingRule,
)
from tangku_agentos.runtime_communication.buses.event_bus import EventBus
from tangku_agentos.runtime_communication.buses.command_bus import CommandBus
from tangku_agentos.runtime_communication.buses.query_bus import QueryBus
from tangku_agentos.runtime_communication.buses.broadcast_bus import BroadcastBus
from tangku_agentos.runtime_communication.buses.request_response import RequestResponseBus

# =============================================================================
# PROTOCOLS
# =============================================================================

from tangku_agentos.runtime_communication.protocols.pubsub import (
    PubSubProtocol,
    QoSLevel,
)
from tangku_agentos.runtime_communication.protocols.request_reply import RequestReplyProtocol
from tangku_agentos.runtime_communication.protocols.stream import StreamProtocol
from tangku_agentos.runtime_communication.protocols.async_task import AsyncTaskProtocol

# =============================================================================
# SERVICES
# =============================================================================

from tangku_agentos.runtime_communication.services.discovery import (
    RuntimeDiscoveryService,
    DiscoveryCriteria,
    DiscoveryResult,
    DiscoveryStrategy,
    ServiceEndpoint,
)
from tangku_agentos.runtime_communication.services.registry import (
    RuntimeRegistry,
    RuntimeInfo,
    RuntimeStatus,
    RuntimeRegistrationOptions,
)
from tangku_agentos.runtime_communication.services.health import (
    RuntimeHealthService,
    HealthStatus,
    HealthCheck,
    HealthCheckResult,
    RuntimeHealth,
    HealthAlert,
)
from tangku_agentos.runtime_communication.services.status import (
    RuntimeStatusManager,
    RuntimeStatusInfo,
    StatusChange,
)
from tangku_agentos.runtime_communication.services.metadata import (
    RuntimeMetadataRegistry,
    MetadataChange,
    MetadataSchema,
    MetadataVersion,
)
from tangku_agentos.runtime_communication.services.context import (
    RuntimeContextManager,
    Context,
    ContextTemplate,
)
from tangku_agentos.runtime_communication.services.session import (
    RuntimeSessionManager,
    Session,
    SessionStatus,
    SessionTemplate,
)

# =============================================================================
# INTERFACES (for type hints)
# =============================================================================

from tangku_agentos.runtime_communication.interfaces import (
    IMessage,
    IMessageHandler,
    IEventHandler,
    ICommandHandler,
    IQueryHandler,
    IMessageBus,
    IEventBus,
    ICommandBus,
    IQueryBus,
    IBroadcastBus,
    IRequestResponseBus,
    IRuntimeRegistry,
    IRuntimeDiscovery,
    IRuntimeHealth,
    IMiddleware,
    IMessageInterceptor,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Core Models
    "Message",
    "MessageType",
    "MessagePriority",
    "MessageStatus",
    "Event",
    "Command",
    "Query",
    "Response",
    "Broadcast",
    "Notification",
    "StreamMessage",
    "AsyncTask",
    "ScheduledTask",
    "MessageEnvelope",
    # Exceptions
    "MessageError",
    "MessageDeliveryError",
    "MessageTimeoutError",
    "MessageValidationError",
    "AuthorizationError",
    "CircuitBreakerOpenError",
    "DuplicateMessageError",
    "RuntimeNotFoundError",
    "RuntimeNotAvailableError",
    "RuntimeCommunicationError",
    "SerializationError",
    "DeserializationError",
    # Buses
    "MessageBus",
    "Subscription",
    "RoutingRule",
    "EventBus",
    "CommandBus",
    "QueryBus",
    "BroadcastBus",
    "RequestResponseBus",
    # Protocols
    "PubSubProtocol",
    "QoSLevel",
    "RequestReplyProtocol",
    "StreamProtocol",
    "AsyncTaskProtocol",
    # Services
    "RuntimeDiscoveryService",
    "DiscoveryCriteria",
    "DiscoveryResult",
    "DiscoveryStrategy",
    "ServiceEndpoint",
    "RuntimeRegistry",
    "RuntimeInfo",
    "RuntimeStatus",
    "RuntimeRegistrationOptions",
    "RuntimeHealthService",
    "HealthStatus",
    "HealthCheck",
    "HealthCheckResult",
    "RuntimeHealth",
    "HealthAlert",
    "RuntimeStatusManager",
    "RuntimeStatusInfo",
    "StatusChange",
    "RuntimeMetadataRegistry",
    "MetadataChange",
    "MetadataSchema",
    "MetadataVersion",
    "RuntimeContextManager",
    "Context",
    "ContextTemplate",
    "RuntimeSessionManager",
    "Session",
    "SessionStatus",
    "SessionTemplate",
    # Interfaces
    "IMessage",
    "IMessageHandler",
    "IEventHandler",
    "ICommandHandler",
    "IQueryHandler",
    "IMessageBus",
    "IEventBus",
    "ICommandBus",
    "IQueryBus",
    "IBroadcastBus",
    "IRequestResponseBus",
    "IRuntimeRegistry",
    "IRuntimeDiscovery",
    "IRuntimeHealth",
    "IMiddleware",
    "IMessageInterceptor",
]
