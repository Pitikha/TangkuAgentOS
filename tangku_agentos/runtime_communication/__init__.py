"""
TangkuAgentOS Runtime Communication Framework

A unified communication layer that allows every runtime inside TangkuAgentOS
to communicate safely, efficiently, and asynchronously.

This framework provides:
- Message Bus for direct and broadcast communication
- Event Bus for publish/subscribe patterns
- Command Bus for command execution
- Query Bus for request/response patterns
- Runtime Services for discovery, registry, health, and metadata
- Reliability features like retry policies, circuit breakers, and dead-letter queues
- Security features including authentication, authorization, and audit logging
- Monitoring and observability with metrics, logging, and tracing

Example usage:
    from tangku_agentos.runtime_communication import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
        RuntimeRegistry,
    )
"""

# Core models
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
)

# Buses
from tangku_agentos.runtime_communication.buses.message_bus import MessageBus
from tangku_agentos.runtime_communication.buses.event_bus import EventBus
from tangku_agentos.runtime_communication.buses.command_bus import CommandBus
from tangku_agentos.runtime_communication.buses.query_bus import QueryBus
from tangku_agentos.runtime_communication.buses.broadcast_bus import BroadcastBus
from tangku_agentos.runtime_communication.buses.request_response import RequestResponseBus

# Protocols
from tangku_agentos.runtime_communication.protocols.pubsub import PubSubProtocol
from tangku_agentos.runtime_communication.protocols.request_reply import RequestReplyProtocol
from tangku_agentos.runtime_communication.protocols.stream import StreamProtocol
from tangku_agentos.runtime_communication.protocols.async_task import AsyncTaskProtocol

# Services
from tangku_agentos.runtime_communication.services.discovery import RuntimeDiscoveryService
from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
from tangku_agentos.runtime_communication.services.health import RuntimeHealthService
from tangku_agentos.runtime_communication.services.status import RuntimeStatusManager
from tangku_agentos.runtime_communication.services.metadata import RuntimeMetadataRegistry
from tangku_agentos.runtime_communication.services.context import RuntimeContextManager
from tangku_agentos.runtime_communication.services.session import RuntimeSessionManager

# Reliability
from tangku_agentos.runtime_communication.reliability.retry import RetryPolicyManager
from tangku_agentos.runtime_communication.reliability.circuit_breaker import CircuitBreaker
from tangku_agentos.runtime_communication.reliability.dead_letter import DeadLetterQueue
from tangku_agentos.runtime_communication.reliability.idempotency import IdempotencyManager
from tangku_agentos.runtime_communication.reliability.deduplication import DuplicateMessageDetector

# Security
from tangku_agentos.runtime_communication.security.authentication import RuntimeAuthenticationService
from tangku_agentos.runtime_communication.security.authorization import RuntimeAuthorizationService
from tangku_agentos.runtime_communication.security.permissions import RuntimePermissionManager
from tangku_agentos.runtime_communication.security.validation import MessageSecurityValidator
from tangku_agentos.runtime_communication.security.audit import AuditLogger

# Monitoring
from tangku_agentos.runtime_communication.monitoring.metrics import CommunicationMetrics
from tangku_agentos.runtime_communication.monitoring.logger import CommunicationLogger
from tangku_agentos.runtime_communication.monitoring.diagnostics import DiagnosticsService
from tangku_agentos.runtime_communication.monitoring.tracing import TraceContextManager

# Middleware
from tangku_agentos.runtime_communication.middleware.base import Middleware
from tangku_agentos.runtime_communication.middleware.validation import ValidationMiddleware
from tangku_agentos.runtime_communication.middleware.security import SecurityMiddleware
from tangku_agentos.runtime_communication.middleware.logging import LoggingMiddleware
from tangku_agentos.runtime_communication.middleware.metrics import MetricsMiddleware
from tangku_agentos.runtime_communication.middleware.tracing import TracingMiddleware

# Utilities
from tangku_agentos.runtime_communication.utils.serialization import MessageSerializer
from tangku_agentos.runtime_communication.utils.validation import MessageValidator

# Interfaces (for type hints)
from tangku_agentos.runtime_communication.interfaces import (
    IMessage,
    IMessageHandler,
    IMessageBus,
    IEventBus,
    ICommandBus,
    IQueryBus,
    IBroadcastBus,
    IRequestResponseBus,
    IRuntimeRegistry,
    IRuntimeDiscovery,
    IRuntimeHealth,
    IMessageSerializer,
    IMessageValidator,
)

__all__ = [
    # Core models
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
    # Buses
    "MessageBus",
    "EventBus",
    "CommandBus",
    "QueryBus",
    "BroadcastBus",
    "RequestResponseBus",
    # Protocols
    "PubSubProtocol",
    "RequestReplyProtocol",
    "StreamProtocol",
    "AsyncTaskProtocol",
    # Services
    "RuntimeDiscoveryService",
    "RuntimeRegistry",
    "RuntimeHealthService",
    "RuntimeStatusManager",
    "RuntimeMetadataRegistry",
    "RuntimeContextManager",
    "RuntimeSessionManager",
    # Reliability
    "RetryPolicyManager",
    "CircuitBreaker",
    "DeadLetterQueue",
    "IdempotencyManager",
    "DuplicateMessageDetector",
    # Security
    "RuntimeAuthenticationService",
    "RuntimeAuthorizationService",
    "RuntimePermissionManager",
    "MessageSecurityValidator",
    "AuditLogger",
    # Monitoring
    "CommunicationMetrics",
    "CommunicationLogger",
    "DiagnosticsService",
    "TraceContextManager",
    # Middleware
    "Middleware",
    "ValidationMiddleware",
    "SecurityMiddleware",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "TracingMiddleware",
    # Utilities
    "MessageSerializer",
    "MessageValidator",
    # Interfaces
    "IMessage",
    "IMessageHandler",
    "IMessageBus",
    "IEventBus",
    "ICommandBus",
    "IQueryBus",
    "IBroadcastBus",
    "IRequestResponseBus",
    "IRuntimeRegistry",
    "IRuntimeDiscovery",
    "IRuntimeHealth",
    "IMessageSerializer",
    "IMessageValidator",
]
