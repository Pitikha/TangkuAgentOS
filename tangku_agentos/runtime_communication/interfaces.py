"""
Runtime Communication Framework - Type Interfaces

This module defines Protocol-based interfaces for the communication framework.
These interfaces enable structural subtyping and provide clear contracts
for all components in the framework.

Using Protocol allows for duck typing while maintaining type safety.
Any class that implements the required methods satisfies the interface.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any, 
    Awaitable, 
    Callable, 
    Dict, 
    Generic, 
    List, 
    Optional, 
    Protocol, 
    runtime_checkable,
    TypeVar,
    Union,
)
from datetime import datetime, timedelta

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

# Type variables for generic interfaces
MessageT = TypeVar('MessageT', bound=Message)
EventT = TypeVar('EventT', bound=Event)
CommandT = TypeVar('CommandT', bound=Command)
QueryT = TypeVar('QueryT', bound=Query)
ResponseT = TypeVar('ResponseT', bound=Response)
ResultT = TypeVar('ResultT')


@runtime_checkable
class IMessage(Protocol):
    """
    Interface for all message types.
    
    All message classes must implement these properties and methods.
    """
    
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]
    payload: Any
    priority: MessagePriority
    created_at: datetime
    expires_at: Optional[datetime]
    correlation_id: Optional[str]
    reply_to: Optional[str]
    status: MessageStatus
    delivery_attempts: int
    max_retries: int
    metadata: Dict[str, Any]
    
    def is_expired(self) -> bool:
        """Check if the message has expired."""
        ...
    
    def should_retry(self) -> bool:
        """Check if the message should be retried."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        ...
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        ...


@runtime_checkable
class IMessageHandler(Protocol[MessageT]):
    """
    Interface for message handlers.
    
    Message handlers process incoming messages of a specific type.
    They must implement the handle method.
    
    Type Parameters:
        MessageT: The type of message this handler processes
    """
    
    async def handle(self, message: MessageT) -> Any:
        """
        Process an incoming message.
        
        Args:
            message: The message to process
            
        Returns:
            The result of processing the message
        """
        ...
    
    def can_handle(self, message: Message) -> bool:
        """
        Check if this handler can process the given message.
        
        Args:
            message: The message to check
            
        Returns:
            True if this handler can process the message, False otherwise
        """
        ...


@runtime_checkable
class IEventHandler(Protocol[EventT]):
    """
    Interface for event handlers.
    
    Event handlers process specific types of events.
    
    Type Parameters:
        EventT: The type of event this handler processes
    """
    
    async def handle_event(self, event: EventT) -> None:
        """
        Process an event.
        
        Args:
            event: The event to process
        """
        ...


@runtime_checkable
class ICommandHandler(Protocol[CommandT, ResultT]):
    """
    Interface for command handlers.
    
    Command handlers execute commands and return results.
    
    Type Parameters:
        CommandT: The type of command this handler processes
        ResultT: The type of result this handler returns
    """
    
    async def handle_command(self, command: CommandT) -> ResultT:
        """
        Execute a command.
        
        Args:
            command: The command to execute
            
        Returns:
            The result of executing the command
        """
        ...


@runtime_checkable
class IQueryHandler(Protocol[QueryT, ResultT]):
    """
    Interface for query handlers.
    
    Query handlers process queries and return results.
    
    Type Parameters:
        QueryT: The type of query this handler processes
        ResultT: The type of result this handler returns
    """
    
    async def handle_query(self, query: QueryT) -> ResultT:
        """
        Process a query.
        
        Args:
            query: The query to process
            
        Returns:
            The result of the query
        """
        ...


@runtime_checkable
class IMessageBus(Protocol):
    """
    Interface for the message bus.
    
    The message bus is the core communication component that handles
    message routing, delivery, and lifecycle management.
    """
    
    async def send(
        self, 
        message: Message, 
        wait_for_response: bool = False,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Send a message.
        
        Args:
            message: The message to send
            wait_for_response: Whether to wait for a response
            timeout: Timeout for response in seconds
            
        Returns:
            Response message if wait_for_response=True, else None
        """
        ...
    
    async def publish(self, message: Message) -> None:
        """
        Publish a message (fire-and-forget).
        
        Args:
            message: The message to publish
        """
        ...
    
    async def request(
        self, 
        message: Message, 
        timeout: Optional[float] = None
    ) -> Message:
        """
        Send a request and wait for a response.
        
        Args:
            message: The request message
            timeout: Timeout in seconds
            
        Returns:
            The response message
            
        Raises:
            MessageTimeoutError: If the request times out
        """
        ...
    
    async def broadcast(
        self, 
        message_type: str, 
        payload: Any,
        sender_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        **kwargs
    ) -> int:
        """
        Broadcast a message to all subscribers.
        
        Args:
            message_type: Type of message to broadcast
            payload: Message payload
            sender_id: ID of the sender
            priority: Message priority
            **kwargs: Additional message properties
            
        Returns:
            Number of subscribers notified
        """
        ...
    
    async def multicast(
        self, 
        message: Message,
        recipient_ids: List[str]
    ) -> int:
        """
        Send a message to multiple specific recipients.
        
        Args:
            message: The message to send
            recipient_ids: List of recipient IDs
            
        Returns:
            Number of recipients
        """
        ...
    
    def subscribe(
        self, 
        message_type: str, 
        handler: IMessageHandler[Message],
        **kwargs
    ) -> str:
        """
        Subscribe a handler to a message type.
        
        Args:
            message_type: Type of message to subscribe to
            handler: Handler to call for matching messages
            **kwargs: Additional subscription options
            
        Returns:
            Subscription ID
        """
        ...
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe a handler.
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            True if subscription was removed, False otherwise
        """
        ...
    
    def get_subscriptions(self, message_type: Optional[str] = None) -> List[str]:
        """
        Get list of subscriptions.
        
        Args:
            message_type: Filter by message type (optional)
            
        Returns:
            List of subscription IDs
        """
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get bus metrics.
        
        Returns:
            Dictionary of metrics
        """
        ...


@runtime_checkable
class IEventBus(Protocol):
    """
    Interface for the event bus.
    
    The event bus is a specialized message bus for publish/subscribe
    communication patterns.
    """
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        Args:
            event: The event to publish
        """
        ...
    
    def subscribe(
        self, 
        event_type: str, 
        handler: IEventHandler[Event],
        **kwargs
    ) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Handler to call for matching events
            **kwargs: Additional subscription options
            
        Returns:
            Subscription ID
        """
        ...
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            subscription_id: ID of the subscription to remove
            
        Returns:
            True if subscription was removed, False otherwise
        """
        ...
    
    async def emit(
        self, 
        event_type: str, 
        payload: Any = None,
        sender_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Emit an event (convenience method).
        
        Args:
            event_type: Type of event
            payload: Event payload
            sender_id: ID of the sender
            **kwargs: Additional event properties
        """
        ...


@runtime_checkable
class ICommandBus(Protocol):
    """
    Interface for the command bus.
    
    The command bus handles command messages with exactly-once execution
    semantics and response handling.
    """
    
    async def send(self, command: Command) -> Any:
        """
        Send a command.
        
        Args:
            command: The command to send
            
        Returns:
            Result of command execution
        """
        ...
    
    def register_handler(
        self, 
        command_type: str, 
        handler: ICommandHandler[Command, Any]
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_type: Type of command to handle
            handler: Handler for the command type
        """
        ...
    
    def unregister_handler(self, command_type: str) -> bool:
        """
        Unregister a command handler.
        
        Args:
            command_type: Type of command
            
        Returns:
            True if handler was removed, False otherwise
        """
        ...


@runtime_checkable
class IQueryBus(Protocol):
    """
    Interface for the query bus.
    
    The query bus handles query messages with request/response semantics
    for information retrieval.
    """
    
    async def ask(self, query: Query) -> Any:
        """
        Ask a query.
        
        Args:
            query: The query to ask
            
        Returns:
            Result of the query
        """
        ...
    
    def register_handler(
        self, 
        query_type: str, 
        handler: IQueryHandler[Query, Any]
    ) -> None:
        """
        Register a query handler.
        
        Args:
            query_type: Type of query to handle
            handler: Handler for the query type
        """
        ...
    
    def unregister_handler(self, query_type: str) -> bool:
        """
        Unregister a query handler.
        
        Args:
            query_type: Type of query
            
        Returns:
            True if handler was removed, False otherwise
        """
        ...


@runtime_checkable
class IBroadcastBus(Protocol):
    """
    Interface for the broadcast bus.
    
    The broadcast bus handles one-to-many communication without
    expecting responses.
    """
    
    async def broadcast(
        self, 
        message: Broadcast,
        channels: Optional[List[str]] = None
    ) -> int:
        """
        Broadcast a message.
        
        Args:
            message: The message to broadcast
            channels: Specific channels to broadcast to
            
        Returns:
            Number of recipients
        """
        ...
    
    async def notify(
        self, 
        notification: Notification,
        requires_ack: bool = False
    ) -> int:
        """
        Send a notification.
        
        Args:
            notification: The notification to send
            requires_ack: Whether acknowledgment is required
            
        Returns:
            Number of recipients
        """
        ...


@runtime_checkable
class IRequestResponseBus(Protocol):
    """
    Interface for request/response communication.
    
    This bus specifically handles the request/response pattern with
    correlation IDs and response matching.
    """
    
    async def request(
        self, 
        request: Message,
        timeout: Optional[float] = None
    ) -> Message:
        """
        Send a request and wait for a response.
        
        Args:
            request: The request message
            timeout: Timeout in seconds
            
        Returns:
            The response message
            
        Raises:
            MessageTimeoutError: If the request times out
        """
        ...
    
    async def reply(
        self, 
        response: Response,
        request_id: Optional[str] = None
    ) -> None:
        """
        Send a reply to a request.
        
        Args:
            response: The response message
            request_id: ID of the original request (optional)
        """
        ...
    
    def register_request_handler(
        self, 
        request_type: str, 
        handler: Callable[[Message], Awaitable[Message]]
    ) -> None:
        """
        Register a handler for a request type.
        
        Args:
            request_type: Type of request to handle
            handler: Handler function
        """
        ...


@runtime_checkable
class IRuntimeRegistry(Protocol):
    """
    Interface for the runtime registry.
    
    The runtime registry maintains information about all registered runtimes
    and their capabilities.
    """
    
    def register(
        self, 
        runtime_id: str,
        runtime_info: Dict[str, Any]
    ) -> None:
        """
        Register a runtime.
        
        Args:
            runtime_id: Unique identifier for the runtime
            runtime_info: Information about the runtime
        """
        ...
    
    def unregister(self, runtime_id: str) -> bool:
        """
        Unregister a runtime.
        
        Args:
            runtime_id: ID of the runtime to unregister
            
        Returns:
            True if runtime was unregistered, False otherwise
        """
        ...
    
    def get(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a runtime.
        
        Args:
            runtime_id: ID of the runtime
            
        Returns:
            Runtime information or None if not found
        """
        ...
    
    def list(self) -> List[str]:
        """
        List all registered runtime IDs.
        
        Returns:
            List of runtime IDs
        """
        ...
    
    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find runtimes with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of runtime IDs with the capability
        """
        ...


@runtime_checkable
class IRuntimeDiscovery(Protocol):
    """
    Interface for runtime discovery service.
    
    The discovery service helps find runtimes based on various criteria.
    """
    
    def discover(
        self, 
        criteria: Dict[str, Any]
    ) -> List[str]:
        """
        Discover runtimes matching criteria.
        
        Args:
            criteria: Discovery criteria
            
        Returns:
            List of matching runtime IDs
        """
        ...
    
    def get_endpoint(
        self, 
        runtime_id: str,
        interface: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the endpoint for a runtime.
        
        Args:
            runtime_id: ID of the runtime
            interface: Specific interface to get endpoint for
            
        Returns:
            Endpoint URL or None if not found
        """
        ...


@runtime_checkable
class IRuntimeHealth(Protocol):
    """
    Interface for runtime health service.
    
    The health service monitors and reports the health status of runtimes.
    """
    
    def get_health(self, runtime_id: str) -> Dict[str, Any]:
        """
        Get health status of a runtime.
        
        Args:
            runtime_id: ID of the runtime
            
        Returns:
            Health status information
        """
        ...
    
    def check_health(self, runtime_id: str) -> bool:
        """
        Check if a runtime is healthy.
        
        Args:
            runtime_id: ID of the runtime
            
        Returns:
            True if runtime is healthy, False otherwise
        """
        ...
    
    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all runtimes.
        
        Returns:
            Dictionary mapping runtime IDs to health status
        """
        ...


@runtime_checkable
class IMessageSerializer(Protocol):
    """
    Interface for message serialization.
    
    Serializers convert messages to/from various formats (JSON, MessagePack, etc.).
    """
    
    def serialize(self, message: Message) -> bytes:
        """
        Serialize a message to bytes.
        
        Args:
            message: The message to serialize
            
        Returns:
            Serialized message bytes
        """
        ...
    
    def deserialize(self, data: bytes) -> Message:
        """
        Deserialize bytes to a message.
        
        Args:
            data: Serialized message bytes
            
        Returns:
            Deserialized message
            
        Raises:
            DeserializationError: If deserialization fails
        """
        ...
    
    def content_type(self) -> str:
        """
        Get the content type of this serializer.
        
        Returns:
            Content type string (e.g., "application/json")
        """
        ...


@runtime_checkable
class IMessageValidator(Protocol):
    """
    Interface for message validation.
    
    Validators ensure messages conform to expected schemas and rules.
    """
    
    def validate(self, message: Message) -> bool:
        """
        Validate a message.
        
        Args:
            message: The message to validate
            
        Returns:
            True if message is valid, False otherwise
        """
        ...
    
    def validate_schema(self, message: Message, schema: Dict[str, Any]) -> bool:
        """
        Validate a message against a specific schema.
        
        Args:
            message: The message to validate
            schema: The schema to validate against
            
        Returns:
            True if message matches schema, False otherwise
        """
        ...
    
    def get_validation_errors(self, message: Message) -> List[str]:
        """
        Get validation errors for a message.
        
        Args:
            message: The message to validate
            
        Returns:
            List of validation error messages
        """
        ...


@runtime_checkable
class IMiddleware(Protocol):
    """
    Interface for middleware components.
    
    Middleware components process messages before/after they are handled.
    """
    
    async def before_handle(
        self, 
        message: Message,
        context: Dict[str, Any]
    ) -> Message:
        """
        Process message before handling.
        
        Args:
            message: The message to process
            context: Processing context
            
        Returns:
            Processed message (can be modified)
        """
        ...
    
    async def after_handle(
        self, 
        message: Message,
        result: Any,
        context: Dict[str, Any]
    ) -> Any:
        """
        Process result after handling.
        
        Args:
            message: The original message
            result: The result from handling
            context: Processing context
            
        Returns:
            Processed result (can be modified)
        """
        ...
    
    async def on_error(
        self, 
        message: Message,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """
        Handle errors during processing.
        
        Args:
            message: The message being processed
            error: The error that occurred
            context: Processing context
        """
        ...


@runtime_checkable
class IMessageInterceptor(Protocol):
    """
    Interface for message interceptors.
    
    Interceptors can intercept and modify messages during processing.
    """
    
    async def intercept(
        self, 
        message: Message,
        next_handler: Callable[[Message], Awaitable[Any]]
    ) -> Any:
        """
        Intercept a message.
        
        Args:
            message: The message to intercept
            next_handler: Next handler in the chain
            
        Returns:
            Result from the handler chain
        """
        ...


@runtime_checkable
class IRetryPolicy(Protocol):
    """
    Interface for retry policies.
    
    Retry policies determine when and how to retry failed operations.
    """
    
    def should_retry(
        self, 
        attempt: int,
        error: Optional[Exception] = None
    ) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            attempt: Current attempt number
            error: The error that occurred (optional)
            
        Returns:
            True if operation should be retried, False otherwise
        """
        ...
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay before the next retry attempt.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Delay in seconds
        """
        ...


@runtime_checkable
class ICircuitBreaker(Protocol):
    """
    Interface for circuit breakers.
    
    Circuit breakers prevent operations from being executed when
    they are likely to fail.
    """
    
    def is_open(self) -> bool:
        """
        Check if the circuit breaker is open.
        
        Returns:
            True if circuit is open, False otherwise
        """
        ...
    
    def is_half_open(self) -> bool:
        """
        Check if the circuit breaker is half-open.
        
        Returns:
            True if circuit is half-open, False otherwise
        """
        ...
    
    def is_closed(self) -> bool:
        """
        Check if the circuit breaker is closed.
        
        Returns:
            True if circuit is closed, False otherwise
        """
        ...
    
    def record_success(self) -> None:
        """Record a successful operation."""
        ...
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        ...
    
    def reset(self) -> None:
        """Reset the circuit breaker state."""
        ...


@runtime_checkable
class IDeadLetterQueue(Protocol):
    """
    Interface for dead letter queues.
    
    Dead letter queues store messages that cannot be delivered or processed.
    """
    
    def add(self, message: Message, error: Optional[str] = None) -> str:
        """
        Add a message to the dead letter queue.
        
        Args:
            message: The message to add
            error: Error that caused the message to be added
            
        Returns:
            ID of the queued message
        """
        ...
    
    def get(self, message_id: str) -> Optional[Message]:
        """
        Get a message from the dead letter queue.
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            The message or None if not found
        """
        ...
    
    def retry(self, message_id: str) -> bool:
        """
        Retry a message from the dead letter queue.
        
        Args:
            message_id: ID of the message to retry
            
        Returns:
            True if message was retried, False otherwise
        """
        ...
    
    def list(self, limit: int = 100) -> List[Message]:
        """
        List messages in the dead letter queue.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        ...
    
    def clear(self) -> int:
        """
        Clear all messages from the dead letter queue.
        
        Returns:
            Number of messages cleared
        """
        ...


@runtime_checkable
class IIdempotencyManager(Protocol):
    """
    Interface for idempotency management.
    
    Idempotency managers ensure operations are executed at most once.
    """
    
    def is_processed(self, idempotency_key: str) -> bool:
        """
        Check if an operation with the given key has been processed.
        
        Args:
            idempotency_key: Unique key for the operation
            
        Returns:
            True if operation has been processed, False otherwise
        """
        ...
    
    def mark_processed(self, idempotency_key: str) -> None:
        """
        Mark an operation as processed.
        
        Args:
            idempotency_key: Unique key for the operation
        """
        ...
    
    def get_result(self, idempotency_key: str) -> Optional[Any]:
        """
        Get the result of a previously processed operation.
        
        Args:
            idempotency_key: Unique key for the operation
            
        Returns:
            Result of the operation or None if not found
        """
        ...
    
    def store_result(self, idempotency_key: str, result: Any) -> None:
        """
        Store the result of an operation.
        
        Args:
            idempotency_key: Unique key for the operation
            result: Result to store
        """
        ...


# Convenience type aliases
MessageHandler = Callable[[Message], Awaitable[Any]]
EventHandler = Callable[[Event], Awaitable[None]]
CommandHandler = Callable[[Command], Awaitable[Any]]
QueryHandler = Callable[[Query], Awaitable[Any]]
MiddlewareFunc = Callable[[Message, Dict[str, Any]], Awaitable[Message]]
ErrorHandler = Callable[[Message, Exception, Dict[str, Any]], Awaitable[None]]

__all__ = [
    # Base interfaces
    "IMessage",
    "IMessageHandler",
    "IEventHandler",
    "ICommandHandler",
    "IQueryHandler",
    # Bus interfaces
    "IMessageBus",
    "IEventBus",
    "ICommandBus",
    "IQueryBus",
    "IBroadcastBus",
    "IRequestResponseBus",
    # Service interfaces
    "IRuntimeRegistry",
    "IRuntimeDiscovery",
    "IRuntimeHealth",
    # Utility interfaces
    "IMessageSerializer",
    "IMessageValidator",
    # Middleware interfaces
    "IMiddleware",
    "IMessageInterceptor",
    # Reliability interfaces
    "IRetryPolicy",
    "ICircuitBreaker",
    "IDeadLetterQueue",
    "IIdempotencyManager",
    # Type aliases
    "MessageHandler",
    "EventHandler",
    "CommandHandler",
    "QueryHandler",
    "MiddlewareFunc",
    "ErrorHandler",
]
