"""
Runtime Communication Framework - Core Message Models

This module defines all message types used in the TangkuAgentOS communication framework.
Each message type serves a specific communication pattern and contains appropriate metadata.

Message Types:
- Message: Base message with common fields
- Event: Asynchronous notification
- Command: Instruction to perform an action
- Query: Request for information
- Response: Reply to a query or command
- Broadcast: Message to multiple recipients
- Notification: One-to-many notification
- StreamMessage: Part of a continuous data stream
- AsyncTask: Asynchronous task execution
- ScheduledTask: Task to be executed at a specific time
- MessageEnvelope: Wrapper for messages with routing and security metadata

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic, Union
import json


T = TypeVar('T')


class MessageType(Enum):
    """
    Enumeration of all supported message types in the communication framework.
    
    Each type represents a specific communication pattern:
    - EVENT: Asynchronous notification, multiple subscribers
    - COMMAND: Instruction to perform an action, single recipient
    - QUERY: Request for information, expects response
    - RESPONSE: Reply to a query or command
    - BROADCAST: Message to all subscribers of a type
    - NOTIFICATION: One-to-many notification
    - STREAM: Part of a continuous data stream
    - ASYNC_TASK: Asynchronous task execution
    - SCHEDULED_TASK: Task to be executed at a specific time
    """
    EVENT = auto()
    COMMAND = auto()
    QUERY = auto()
    RESPONSE = auto()
    BROADCAST = auto()
    NOTIFICATION = auto()
    STREAM = auto()
    ASYNC_TASK = auto()
    SCHEDULED_TASK = auto()


class MessagePriority(Enum):
    """
    Message priority levels for quality of service.
    
    Higher priority messages are processed first. The numeric values allow
    for easy comparison: lower value = higher priority.
    
    Attributes:
        LOW: Background tasks, non-critical operations
        NORMAL: Standard operations, default priority
        HIGH: Important operations that should be processed quickly
        CRITICAL: System-critical operations, must be processed immediately
    """
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


class MessageStatus(Enum):
    """
    Lifecycle status of a message.
    
    Tracks the state of a message from creation to final delivery or failure.
    
    Attributes:
        PENDING: Message created but not yet sent
        SENT: Message has been sent to the bus
        DELIVERED: Message successfully delivered to recipient
        PROCESSING: Message is being processed by handler
        FAILED: Message delivery or processing failed
        EXPIRED: Message expired before delivery
        CANCELLED: Message was cancelled
        RETRYING: Message is being retried
        DEAD_LETTER: Message moved to dead letter queue
    """
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSING = "processing"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class Message:
    """
    Base message model with full routing and lifecycle information.
    
    This is the foundation for all message types in the communication framework.
    It contains common fields for identification, routing, priority, and lifecycle tracking.
    
    Attributes:
        message_id: Unique identifier for the message (UUID)
        message_type: Type of message (from MessageType enum)
        sender_id: Identifier of the runtime that sent the message
        recipient_id: Identifier of the intended recipient (None for broadcast)
        payload: The actual message content/data
        priority: Message priority level (default: NORMAL)
        created_at: Timestamp when message was created
        expires_at: Timestamp when message expires (None for no expiration)
        correlation_id: Links related messages together
        reply_to: Message ID to reply to (for request/response pattern)
        conversation_id: Identifier for a conversation/thread
        status: Current lifecycle status of the message
        delivery_attempts: Number of delivery attempts made
        max_retries: Maximum number of retry attempts (default: 3)
        metadata: Additional key-value metadata
        tags: Set of tags for filtering and routing
        headers: HTTP-style headers for additional routing info
    
    Example:
        >>> message = Message(
        ...     message_type=MessageType.COMMAND,
        ...     sender_id="kernel_runtime",
        ...     recipient_id="memory_runtime",
        ...     payload={"action": "store", "data": "test"},
        ...     priority=MessagePriority.HIGH
        ... )
        >>> message.message_id
        '...'
        >>> message.is_expired()
        False
    """
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.EVENT
    sender_id: str = ""
    recipient_id: Optional[str] = None
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    conversation_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    delivery_attempts: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default correlation ID if not provided."""
        if self.correlation_id is None:
            self.correlation_id = self.message_id
        if self.conversation_id is None:
            self.conversation_id = self.correlation_id
    
    def is_expired(self) -> bool:
        """
        Check if the message has expired.
        
        Returns:
            True if message has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def should_retry(self) -> bool:
        """
        Check if the message should be retried.
        
        Returns:
            True if message failed and has retries remaining, False otherwise
        """
        return (
            self.status == MessageStatus.FAILED
            and self.delivery_attempts < self.max_retries
        )
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the message for filtering and routing.
        
        Args:
            tag: Tag to add
        """
        self.tags.add(tag)
    
    def add_tags(self, tags: Set[str]) -> None:
        """
        Add multiple tags to the message.
        
        Args:
            tags: Set of tags to add
        """
        self.tags.update(tags)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the message.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def add_header(self, key: str, value: str) -> None:
        """
        Add a header to the message.
        
        Args:
            key: Header key
            value: Header value
        """
        self.headers[key] = value
    
    def increment_delivery_attempts(self) -> None:
        """Increment the delivery attempt counter."""
        self.delivery_attempts += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary representation.
        
        Returns:
            Dictionary containing all message fields
        """
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.name,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "payload": self.payload,
            "priority": self.priority.name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "conversation_id": self.conversation_id,
            "status": self.status.value,
            "delivery_attempts": self.delivery_attempts,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "tags": list(self.tags),
            "headers": self.headers,
        }
    
    def to_json(self) -> str:
        """
        Convert message to JSON string.
        
        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        Create a Message from a dictionary.
        
        Args:
            data: Dictionary containing message fields
            
        Returns:
            Message instance
        """
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=MessageType[data.get("message_type", "EVENT")],
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            payload=data.get("payload"),
            priority=MessagePriority[data.get("priority", "NORMAL")],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            conversation_id=data.get("conversation_id"),
            status=MessageStatus(data.get("status", "PENDING")),
            delivery_attempts=data.get("delivery_attempts", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            headers=data.get("headers", {}),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """
        Create a Message from a JSON string.
        
        Args:
            json_str: JSON string representation of a message
            
        Returns:
            Message instance
        """
        return cls.from_dict(json.loads(json_str))


@dataclass
class Event(Message):
    """
    Event message for publish/subscribe communication pattern.
    
    Events are asynchronous notifications that can have multiple subscribers.
    They represent something that has happened in the system.
    
    Attributes:
        event_type: Specific type of event (e.g., "runtime.started")
        source: Source of the event
        severity: Event severity level (debug, info, warning, error, critical)
        timestamp: When the event occurred
    
    Example:
        >>> event = Event(
        ...     message_type=MessageType.EVENT,
        ...     sender_id="kernel_runtime",
        ...     event_type="runtime.started",
        ...     source="kernel",
        ...     severity="info",
        ...     payload={"runtime_id": "memory_runtime"}
        ... )
    """
    
    event_type: str = ""
    source: str = ""
    severity: str = "info"  # debug, info, warning, error, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Initialize message type to EVENT."""
        super().__post_init__()
        self.message_type = MessageType.EVENT
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "event_type": self.event_type,
            "source": self.source,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
        })
        return base_dict


@dataclass
class Command(Message):
    """
    Command message for instruction-based communication.
    
    Commands are instructions to perform a specific action. They are typically
    sent to a single recipient and expect a response indicating success or failure.
    
    Attributes:
        command_type: Specific type of command (e.g., "store.memory")
        parameters: Command parameters
        expected_response_type: Type of response expected
        timeout: Command execution timeout in seconds
    
    Example:
        >>> command = Command(
        ...     message_type=MessageType.COMMAND,
        ...     sender_id="workflow_runtime",
        ...     recipient_id="memory_runtime",
        ...     command_type="store.memory",
        ...     payload={"key": "test", "value": "data"},
        ...     expected_response_type="StoreResponse"
        ... )
    """
    
    command_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_response_type: Optional[str] = None
    timeout: float = 30.0  # seconds
    
    def __post_init__(self):
        """Initialize message type to COMMAND."""
        super().__post_init__()
        self.message_type = MessageType.COMMAND
        # Store parameters in payload if not already set
        if self.payload is None and self.parameters:
            self.payload = self.parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "command_type": self.command_type,
            "parameters": self.parameters,
            "expected_response_type": self.expected_response_type,
            "timeout": self.timeout,
        })
        return base_dict


@dataclass
class Query(Message):
    """
    Query message for information retrieval.
    
    Queries are requests for information. They are sent to a single recipient
    and expect a Response message containing the requested data.
    
    Attributes:
        query_type: Specific type of query (e.g., "get.memory")
        parameters: Query parameters
        expected_response_type: Type of response expected
        timeout: Query execution timeout in seconds
    
    Example:
        >>> query = Query(
        ...     message_type=MessageType.QUERY,
        ...     sender_id="reasoning_runtime",
        ...     recipient_id="memory_runtime",
        ...     query_type="get.memory",
        ...     payload={"key": "test"},
        ...     expected_response_type="MemoryResponse"
        ... )
    """
    
    query_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_response_type: Optional[str] = None
    timeout: float = 30.0  # seconds
    
    def __post_init__(self):
        """Initialize message type to QUERY."""
        super().__post_init__()
        self.message_type = MessageType.QUERY
        # Store parameters in payload if not already set
        if self.payload is None and self.parameters:
            self.payload = self.parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "query_type": self.query_type,
            "parameters": self.parameters,
            "expected_response_type": self.expected_response_type,
            "timeout": self.timeout,
        })
        return base_dict


@dataclass
class Response(Message):
    """
    Response message for query and command replies.
    
    Responses are replies to Query or Command messages. They contain the
    result of the operation or an error if the operation failed.
    
    Attributes:
        request_id: ID of the original request message
        is_success: Whether the operation was successful
        error: Error information if operation failed
        result: Result data if operation succeeded
    
    Example:
        >>> response = Response(
        ...     message_type=MessageType.RESPONSE,
        ...     sender_id="memory_runtime",
        ...     recipient_id="reasoning_runtime",
        ...     request_id="abc-123",
        ...     is_success=True,
        ...     result={"key": "test", "value": "data"}
        ... )
    """
    
    request_id: str = ""
    is_success: bool = True
    error: Optional[str] = None
    result: Any = None
    
    def __post_init__(self):
        """Initialize message type to RESPONSE."""
        super().__post_init__()
        self.message_type = MessageType.RESPONSE
        # Set reply_to to request_id if not already set
        if self.reply_to is None and self.request_id:
            self.reply_to = self.request_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "request_id": self.request_id,
            "is_success": self.is_success,
            "error": self.error,
            "result": self.result,
        })
        return base_dict
    
    @classmethod
    def success(cls, request_id: str, result: Any, **kwargs) -> "Response":
        """
        Create a successful response.
        
        Args:
            request_id: ID of the original request
            result: Result data
            **kwargs: Additional message fields
            
        Returns:
            Success Response instance
        """
        return cls(
            request_id=request_id,
            is_success=True,
            result=result,
            **kwargs
        )
    
    @classmethod
    def error(cls, request_id: str, error: str, **kwargs) -> "Response":
        """
        Create an error response.
        
        Args:
            request_id: ID of the original request
            error: Error message
            **kwargs: Additional message fields
            
        Returns:
            Error Response instance
        """
        return cls(
            request_id=request_id,
            is_success=False,
            error=error,
            **kwargs
        )


@dataclass
class Broadcast(Message):
    """
    Broadcast message for one-to-many communication.
    
    Broadcast messages are sent to all subscribers of a specific message type.
    They do not expect responses and are typically used for notifications.
    
    Attributes:
        broadcast_type: Type of broadcast (e.g., "system.notification")
        channels: Specific channels to broadcast to (None for all)
    
    Example:
        >>> broadcast = Broadcast(
        ...     message_type=MessageType.BROADCAST,
        ...     sender_id="kernel_runtime",
        ...     broadcast_type="system.shutdown",
        ...     payload={"reason": "maintenance"},
        ...     priority=MessagePriority.HIGH
        ... )
    """
    
    broadcast_type: str = ""
    channels: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize message type to BROADCAST."""
        super().__post_init__()
        self.message_type = MessageType.BROADCAST
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert broadcast to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "broadcast_type": self.broadcast_type,
            "channels": self.channels,
        })
        return base_dict


@dataclass
class Notification(Message):
    """
    Notification message for one-to-many communication with acknowledgment.
    
    Notifications are similar to broadcasts but can request acknowledgment
    from recipients. They are typically used for important system events.
    
    Attributes:
        notification_type: Type of notification
        requires_ack: Whether acknowledgment is required
        ack_timeout: Timeout for acknowledgment in seconds
        acked_by: List of runtime IDs that have acknowledged
    
    Example:
        >>> notification = Notification(
        ...     message_type=MessageType.NOTIFICATION,
        ...     sender_id="kernel_runtime",
        ...     notification_type="runtime.updated",
        ...     payload={"runtime_id": "memory_runtime"},
        ...     requires_ack=True,
        ...     ack_timeout=60.0
        ... )
    """
    
    notification_type: str = ""
    requires_ack: bool = False
    ack_timeout: float = 60.0  # seconds
    acked_by: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize message type to NOTIFICATION."""
        super().__post_init__()
        self.message_type = MessageType.NOTIFICATION
    
    def add_ack(self, runtime_id: str) -> None:
        """
        Add an acknowledgment from a runtime.
        
        Args:
            runtime_id: ID of the runtime acknowledging
        """
        if runtime_id not in self.acked_by:
            self.acked_by.append(runtime_id)
    
    def is_fully_acked(self, expected_runtimes: List[str]) -> bool:
        """
        Check if all expected runtimes have acknowledged.
        
        Args:
            expected_runtimes: List of runtime IDs that should acknowledge
            
        Returns:
            True if all expected runtimes have acknowledged, False otherwise
        """
        if not self.requires_ack:
            return True
        return set(expected_runtimes).issubset(set(self.acked_by))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "notification_type": self.notification_type,
            "requires_ack": self.requires_ack,
            "ack_timeout": self.ack_timeout,
            "acked_by": self.acked_by,
        })
        return base_dict


@dataclass
class StreamMessage(Message):
    """
    Stream message for continuous data flow.
    
    Stream messages are part of a continuous data stream. They support
    backpressure and can be chunked for large data transfers.
    
    Attributes:
        stream_id: Unique identifier for the stream
        sequence_number: Sequence number in the stream
        is_start: Whether this is the start of a stream
        is_end: Whether this is the end of a stream
        chunk_size: Size of this chunk in bytes
        total_size: Total size of the stream in bytes (if known)
        backpressure: Whether backpressure is being applied
    
    Example:
        >>> stream_msg = StreamMessage(
        ...     message_type=MessageType.STREAM,
        ...     sender_id="data_processor",
        ...     recipient_id="storage_runtime",
        ...     stream_id="data_stream_123",
        ...     sequence_number=1,
        ...     is_start=True,
        ...     is_end=False,
        ...     payload=b"chunk1_data",
        ...     chunk_size=1024
        ... )
    """
    
    stream_id: str = ""
    sequence_number: int = 0
    is_start: bool = False
    is_end: bool = False
    chunk_size: int = 0
    total_size: Optional[int] = None
    backpressure: bool = False
    
    def __post_init__(self):
        """Initialize message type to STREAM."""
        super().__post_init__()
        self.message_type = MessageType.STREAM
        if not self.stream_id:
            self.stream_id = self.message_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stream message to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "stream_id": self.stream_id,
            "sequence_number": self.sequence_number,
            "is_start": self.is_start,
            "is_end": self.is_end,
            "chunk_size": self.chunk_size,
            "total_size": self.total_size,
            "backpressure": self.backpressure,
        })
        return base_dict


@dataclass
class AsyncTask(Message):
    """
    Async task message for asynchronous task execution.
    
    Async tasks are long-running operations that execute asynchronously.
    They can report progress and can be cancelled.
    
    Attributes:
        task_id: Unique identifier for the task
        task_type: Type of task to execute
        parameters: Task parameters
        progress: Current progress percentage (0-100)
        result: Task result (when completed)
        error: Error information (if failed)
        is_cancelled: Whether the task was cancelled
        is_completed: Whether the task has completed
    
    Example:
        >>> task = AsyncTask(
        ...     message_type=MessageType.ASYNC_TASK,
        ...     sender_id="workflow_runtime",
        ...     task_id="task_123",
        ...     task_type="data_processing",
        ...     payload={"data": "..."},
        ...     timeout=3600.0  # 1 hour
        ... )
    """
    
    task_id: str = ""
    task_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    progress: int = 0  # 0-100
    result: Any = None
    error: Optional[str] = None
    is_cancelled: bool = False
    is_completed: bool = False
    
    def __post_init__(self):
        """Initialize message type to ASYNC_TASK."""
        super().__post_init__()
        self.message_type = MessageType.ASYNC_TASK
        if not self.task_id:
            self.task_id = self.message_id
    
    def update_progress(self, progress: int, result: Any = None) -> None:
        """
        Update task progress.
        
        Args:
            progress: New progress percentage (0-100)
            result: Partial result (optional)
        """
        self.progress = max(0, min(100, progress))
        if result is not None:
            self.result = result
        if self.progress >= 100:
            self.is_completed = True
    
    def complete(self, result: Any = None) -> None:
        """
        Mark task as completed.
        
        Args:
            result: Final result
        """
        self.progress = 100
        self.is_completed = True
        if result is not None:
            self.result = result
    
    def fail(self, error: str) -> None:
        """
        Mark task as failed.
        
        Args:
            error: Error message
        """
        self.error = error
        self.is_completed = True
    
    def cancel(self) -> None:
        """Cancel the task."""
        self.is_cancelled = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert async task to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "task_id": self.task_id,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "is_cancelled": self.is_cancelled,
            "is_completed": self.is_completed,
        })
        return base_dict


@dataclass
class ScheduledTask(Message):
    """
    Scheduled task message for delayed execution.
    
    Scheduled tasks are executed at a specific time or after a delay.
    They can be recurring or one-time.
    
    Attributes:
        task_id: Unique identifier for the task
        task_type: Type of task to execute
        scheduled_time: When the task should be executed
        delay: Delay before execution in seconds
        recurrence: Recurrence pattern (None for one-time)
        parameters: Task parameters
    
    Example:
        >>> scheduled_task = ScheduledTask(
        ...     message_type=MessageType.SCHEDULED_TASK,
        ...     sender_id="scheduler",
        ...     task_id="scheduled_123",
        ...     task_type="cleanup",
        ...     scheduled_time=datetime.utcnow() + timedelta(hours=1),
        ...     payload={"resource": "temp_files"}
        ... )
    """
    
    task_id: str = ""
    task_type: str = ""
    scheduled_time: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=1))
    delay: Optional[float] = None  # seconds
    recurrence: Optional[str] = None  # e.g., "0 * * * *" (cron)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize message type to SCHEDULED_TASK."""
        super().__post_init__()
        self.message_type = MessageType.SCHEDULED_TASK
        if not self.task_id:
            self.task_id = self.message_id
        # Calculate scheduled_time from delay if provided
        if self.delay is not None:
            self.scheduled_time = datetime.utcnow() + timedelta(seconds=self.delay)
    
    def is_due(self) -> bool:
        """
        Check if the task is due for execution.
        
        Returns:
            True if scheduled time has passed, False otherwise
        """
        return datetime.utcnow() >= self.scheduled_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduled task to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "task_id": self.task_id,
            "task_type": self.task_type,
            "scheduled_time": self.scheduled_time.isoformat(),
            "delay": self.delay,
            "recurrence": self.recurrence,
            "parameters": self.parameters,
        })
        return base_dict


@dataclass
class MessageEnvelope:
    """
    Envelope wrapper for messages with routing and security metadata.
    
    The envelope wraps a message and adds additional metadata for routing,
    security, and processing. It's used for inter-runtime communication.
    
    Attributes:
        message: The wrapped message
        source_runtime: Runtime that sent the message
        target_runtime: Runtime that should receive the message
        routing_key: Routing key for message routing
        exchange: Exchange name for message routing
        security_context: Security context for authentication/authorization
        tracing_context: Distributed tracing context
        compression: Compression type (None, gzip, etc.)
        encryption: Encryption type (None, aes, etc.)
        signature: Message signature for integrity verification
    
    Example:
        >>> message = Command(...)
        >>> envelope = MessageEnvelope(
        ...     message=message,
        ...     source_runtime="workflow_runtime",
        ...     target_runtime="memory_runtime",
        ...     routing_key="commands.memory",
        ...     security_context={"user_id": "admin", "roles": ["admin"]}
        ... )
    """
    
    message: Message
    source_runtime: str = ""
    target_runtime: Optional[str] = None
    routing_key: str = ""
    exchange: str = "default"
    security_context: Dict[str, Any] = field(default_factory=dict)
    tracing_context: Dict[str, str] = field(default_factory=dict)
    compression: Optional[str] = None
    encryption: Optional[str] = None
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert envelope to dictionary.
        
        Returns:
            Dictionary containing envelope and message data
        """
        return {
            "envelope": {
                "source_runtime": self.source_runtime,
                "target_runtime": self.target_runtime,
                "routing_key": self.routing_key,
                "exchange": self.exchange,
                "security_context": self.security_context,
                "tracing_context": self.tracing_context,
                "compression": self.compression,
                "encryption": self.encryption,
                "signature": self.signature,
            },
            "message": self.message.to_dict(),
        }
    
    def to_json(self) -> str:
        """
        Convert envelope to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageEnvelope":
        """
        Create an envelope from a dictionary.
        
        Args:
            data: Dictionary containing envelope and message data
            
        Returns:
            MessageEnvelope instance
        """
        envelope_data = data.get("envelope", {})
        message_data = data.get("message", {})
        
        # Determine message type and create appropriate message
        message_type = message_data.get("message_type", "EVENT")
        message_class = {
            "EVENT": Event,
            "COMMAND": Command,
            "QUERY": Query,
            "RESPONSE": Response,
            "BROADCAST": Broadcast,
            "NOTIFICATION": Notification,
            "STREAM": StreamMessage,
            "ASYNC_TASK": AsyncTask,
            "SCHEDULED_TASK": ScheduledTask,
        }.get(message_type, Message)
        
        message = message_class.from_dict(message_data)
        
        return cls(
            message=message,
            source_runtime=envelope_data.get("source_runtime", ""),
            target_runtime=envelope_data.get("target_runtime"),
            routing_key=envelope_data.get("routing_key", ""),
            exchange=envelope_data.get("exchange", "default"),
            security_context=envelope_data.get("security_context", {}),
            tracing_context=envelope_data.get("tracing_context", {}),
            compression=envelope_data.get("compression"),
            encryption=envelope_data.get("encryption"),
            signature=envelope_data.get("signature"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "MessageEnvelope":
        """
        Create an envelope from a JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            MessageEnvelope instance
        """
        return cls.from_dict(json.loads(json_str))
