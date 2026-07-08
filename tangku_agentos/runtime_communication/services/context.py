"""
Runtime Communication Framework - Runtime Context Manager

The RuntimeContextManager provides context propagation for TangkuAgentOS
runtime communication. It enables:
- Context creation and management
- Context propagation across runtime boundaries
- Context storage and retrieval
- Context validation
- Context cleanup

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Message

logger = logging.getLogger(__name__)


@dataclass
class Context:
    """
    Represents a communication context for runtime interactions.

    A context contains information that should be propagated across
    runtime boundaries during communication. This includes:
    - Correlation IDs for tracing
    - Authentication tokens
    - Request IDs
    - Custom context values

    Attributes:
        context_id: Unique identifier for the context.
        correlation_id: Correlation ID for tracing.
        conversation_id: Conversation ID for threading.
        request_id: Request ID for the current request.
        parent_context_id: ID of the parent context (for nested contexts).
        runtime_id: ID of the runtime that created the context.
        user_id: ID of the user associated with the context.
        session_id: ID of the session associated with the context.
        values: Custom context values.
        metadata: Context metadata.
        created_at: When the context was created.
        expires_at: When the context expires.
        is_active: Whether the context is active.
    """

    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    parent_context_id: Optional[str] = None
    runtime_id: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        """Initialize default correlation ID if not provided."""
        if self.correlation_id is None:
            self.correlation_id = self.context_id
        if self.conversation_id is None:
            self.conversation_id = self.correlation_id

    def is_expired(self) -> bool:
        """Check if the context has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.values[key] = value

    def delete(self, key: str) -> bool:
        """Delete a context value."""
        if key in self.values:
            del self.values[key]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "context_id": self.context_id,
            "correlation_id": self.correlation_id,
            "conversation_id": self.conversation_id,
            "request_id": self.request_id,
            "parent_context_id": self.parent_context_id,
            "runtime_id": self.runtime_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "values": self.values,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """Create context from dictionary."""
        return cls(
            context_id=data.get("context_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id"),
            conversation_id=data.get("conversation_id"),
            request_id=data.get("request_id"),
            parent_context_id=data.get("parent_context_id"),
            runtime_id=data.get("runtime_id", ""),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            values=data.get("values", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
            is_active=data.get("is_active", True),
        )

    def to_headers(self) -> Dict[str, str]:
        """
        Convert context to headers for message propagation.

        Returns:
            Dictionary of headers.
        """
        headers = {}
        if self.context_id:
            headers["X-Context-ID"] = self.context_id
        if self.correlation_id:
            headers["X-Correlation-ID"] = self.correlation_id
        if self.conversation_id:
            headers["X-Conversation-ID"] = self.conversation_id
        if self.request_id:
            headers["X-Request-ID"] = self.request_id
        if self.parent_context_id:
            headers["X-Parent-Context-ID"] = self.parent_context_id
        if self.runtime_id:
            headers["X-Runtime-ID"] = self.runtime_id
        if self.user_id:
            headers["X-User-ID"] = self.user_id
        if self.session_id:
            headers["X-Session-ID"] = self.session_id
        return headers

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "Context":
        """
        Create context from headers.

        Args:
            headers: Dictionary of headers.

        Returns:
            Context instance.
        """
        return cls(
            context_id=headers.get("X-Context-ID"),
            correlation_id=headers.get("X-Correlation-ID"),
            conversation_id=headers.get("X-Conversation-ID"),
            request_id=headers.get("X-Request-ID"),
            parent_context_id=headers.get("X-Parent-Context-ID"),
            runtime_id=headers.get("X-Runtime-ID", ""),
            user_id=headers.get("X-User-ID"),
            session_id=headers.get("X-Session-ID"),
        )

    def child(self, **kwargs) -> "Context":
        """
        Create a child context.

        Args:
            **kwargs: Additional context attributes.

        Returns:
            New child context.
        """
        return Context(
            context_id=str(uuid.uuid4()),
            correlation_id=self.correlation_id,
            conversation_id=self.conversation_id,
            request_id=kwargs.get("request_id", self.request_id),
            parent_context_id=self.context_id,
            runtime_id=kwargs.get("runtime_id", self.runtime_id),
            user_id=kwargs.get("user_id", self.user_id),
            session_id=kwargs.get("session_id", self.session_id),
            values=self.values.copy(),
            metadata=self.metadata.copy(),
            created_at=datetime.utcnow(),
            expires_at=kwargs.get("expires_at", self.expires_at),
            is_active=True,
        )


@dataclass
class ContextTemplate:
    """
    Template for creating contexts with default values.

    Attributes:
        name: Name of the template.
        default_values: Default context values.
        default_metadata: Default context metadata.
        ttl: Default time-to-live in seconds.
    """

    name: str
    default_values: Dict[str, Any] = field(default_factory=dict)
    default_metadata: Dict[str, Any] = field(default_factory=dict)
    ttl: float = 3600.0  # 1 hour


class RuntimeContextManager:
    """
    Context manager for TangkuAgentOS runtime communication.

    The RuntimeContextManager provides context propagation capabilities
    for runtime communication. It enables contexts to be created, stored,
    retrieved, and propagated across runtime boundaries.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.context import RuntimeContextManager
        >>> 
        >>> context_manager = RuntimeContextManager()
        >>> 
        >>> # Create a context
        >>> context = context_manager.create(
        ...     runtime_id="kernel_runtime",
        ...     user_id="user123",
        ...     values={"theme": "dark"}
        ... )
        >>> 
        >>> # Get current context
        >>> current = context_manager.get_current()
        >>> 
        >>> # Use context manager
        >>> async with context_manager.context(context):
        ...     # Context is active here
        ...     pass

    Attributes:
        default_ttl: Default time-to-live for contexts in seconds.
        max_contexts: Maximum number of contexts to store.
    """

    def __init__(
        self,
        default_ttl: float = 3600.0,  # 1 hour
        max_contexts: int = 10000,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime context manager.

        Args:
            default_ttl: Default time-to-live for contexts in seconds.
            max_contexts: Maximum number of contexts to store.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Context storage: context_id -> Context
        self._contexts: Dict[str, Context] = {}
        self._contexts_lock = asyncio.Lock()
        self._max_contexts = max_contexts

        # Current context (thread-local or async-local)
        self._current_context: Optional[Context] = None

        # Context templates: template_name -> ContextTemplate
        self._templates: Dict[str, ContextTemplate] = {}
        self._templates_lock = asyncio.Lock()

        # Context change callbacks
        self._on_create: List[Callable[[Context], None]] = []
        self._on_destroy: List[Callable[[Context], None]] = []

        # Configuration
        self._default_ttl = default_ttl

        # Metrics
        self._metrics: Dict[str, Any] = {
            "contexts_created": 0,
            "contexts_destroyed": 0,
            "contexts_active": 0,
            "contexts_expired": 0,
            "context_queries": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"RuntimeContextManager initialized with ttl={default_ttl}, "
            f"max_contexts={max_contexts}"
        )

    def create(
        self,
        runtime_id: str = "",
        correlation_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
        parent_context: Optional[Context] = None,
    ) -> Context:
        """
        Create a new context.

        Args:
            runtime_id: ID of the runtime creating the context.
            correlation_id: Correlation ID for tracing.
            conversation_id: Conversation ID for threading.
            request_id: Request ID for the current request.
            user_id: ID of the user associated with the context.
            session_id: ID of the session associated with the context.
            values: Custom context values.
            metadata: Context metadata.
            ttl: Time-to-live in seconds.
            parent_context: Parent context for nested contexts.

        Returns:
            New context.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create(
            ...     runtime_id="kernel_runtime",
            ...     user_id="user123"
            ... )
        """
        # Use parent context if provided
        if parent_context is not None:
            context = parent_context.child(
                runtime_id=runtime_id,
                correlation_id=correlation_id,
                conversation_id=conversation_id,
                request_id=request_id,
                user_id=user_id,
                session_id=session_id,
                values=values,
                metadata=metadata,
                ttl=ttl,
            )
        else:
            context = Context(
                runtime_id=runtime_id,
                correlation_id=correlation_id,
                conversation_id=conversation_id,
                request_id=request_id,
                user_id=user_id,
                session_id=session_id,
                values=values or {},
                metadata=metadata or {},
            )

        # Set expiration
        if ttl is not None:
            context.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        elif self._default_ttl > 0:
            context.expires_at = datetime.utcnow() + timedelta(
                seconds=self._default_ttl
            )

        # Store context
        asyncio.run(self._store_context(context))

        # Call create callbacks
        for callback in self._on_create:
            try:
                callback(context)
            except Exception as e:
                logger.error(f"Error in context create callback: {e}")

        if self._enable_logging:
            logger.debug(f"Context created: {context.context_id}")

        return context

    async def _store_context(self, context: Context) -> None:
        """Store a context."""
        async with self._contexts_lock:
            # Clean up expired contexts if at capacity
            if len(self._contexts) >= self._max_contexts:
                self._cleanup_expired()

            self._contexts[context.context_id] = context

            async with self._metrics_lock:
                self._metrics["contexts_created"] += 1
                self._metrics["contexts_active"] += 1

    def get(self, context_id: str) -> Optional[Context]:
        """
        Get a context by ID.

        Args:
            context_id: ID of the context.

        Returns:
            Context if found, None otherwise.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create()
            >>> retrieved = context_manager.get(context.context_id)
        """
        async with self._contexts_lock:
            async with self._metrics_lock:
                self._metrics["context_queries"] += 1

            return self._contexts.get(context_id)

    def get_current(self) -> Optional[Context]:
        """
        Get the current context.

        Returns:
            Current context or None if not set.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create()
            >>> context_manager.set_current(context)
            >>> current = context_manager.get_current()
        """
        return self._current_context

    def set_current(self, context: Optional[Context]) -> None:
        """
        Set the current context.

        Args:
            context: Context to set as current.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create()
            >>> context_manager.set_current(context)
        """
        self._current_context = context

    @asynccontextmanager
    async def context(
        self, context: Optional[Context] = None
    ) -> AsyncGenerator[Context, None]:
        """
        Context manager for setting the current context.

        Args:
            context: Context to use (creates new if not provided).

        Yields:
            The context.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> async with context_manager.context() as ctx:
            ...     ctx.set("key", "value")
            ...     current = context_manager.get_current()
        """
        if context is None:
            context = self.create()

        # Save previous context
        previous = self._current_context

        try:
            self.set_current(context)
            yield context
        finally:
            # Restore previous context
            self.set_current(previous)

    def destroy(self, context_id: str) -> bool:
        """
        Destroy a context.

        Args:
            context_id: ID of the context to destroy.

        Returns:
            True if context was destroyed, False otherwise.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create()
            >>> context_manager.destroy(context.context_id)
            True
        """
        return asyncio.run(self._destroy_async(context_id))

    async def _destroy_async(self, context_id: str) -> bool:
        """Async version of destroy."""
        async with self._contexts_lock:
            if context_id not in self._contexts:
                return False

            context = self._contexts[context_id]

            # Mark as inactive
            context.is_active = False

            # Remove from storage
            del self._contexts[context_id]

            # Update metrics
            async with self._metrics_lock:
                self._metrics["contexts_destroyed"] += 1
                self._metrics["contexts_active"] -= 1

            # Call destroy callbacks
            for callback in self._on_destroy:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Error in context destroy callback: {e}")

            if self._enable_logging:
                logger.debug(f"Context destroyed: {context_id}")

            return True

    def cleanup(self) -> int:
        """
        Clean up expired contexts.

        Returns:
            Number of contexts cleaned up.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> count = context_manager.cleanup()
        """
        return asyncio.run(self._cleanup_async())

    async def _cleanup_async(self) -> int:
        """Async version of cleanup."""
        count = 0

        async with self._contexts_lock:
            expired = [
                cid
                for cid, ctx in self._contexts.items()
                if ctx.is_expired() or not ctx.is_active
            ]

            for cid in expired:
                del self._contexts[cid]
                count += 1

                async with self._metrics_lock:
                    self._metrics["contexts_expired"] += 1
                    self._metrics["contexts_active"] -= 1

        if count > 0 and self._enable_logging:
            logger.info(f"Cleaned up {count} expired contexts")

        return count

    def _cleanup_expired(self) -> None:
        """Clean up expired contexts (internal)."""
        # This is called internally when at capacity
        expired = [
            cid
            for cid, ctx in self._contexts.items()
            if ctx.is_expired() or not ctx.is_active
        ]

        for cid in expired:
            del self._contexts[cid]

            async with self._metrics_lock:
                self._metrics["contexts_expired"] += 1
                self._metrics["contexts_active"] -= 1

    def register_template(self, template: ContextTemplate) -> None:
        """
        Register a context template.

        Args:
            template: Template to register.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> template = ContextTemplate(
            ...     name="api_request",
            ...     default_values={"request_id": ""},
            ...     ttl=60.0
            ... )
            >>> context_manager.register_template(template)
        """
        asyncio.run(self._register_template_async(template))

    async def _register_template_async(self, template: ContextTemplate) -> None:
        """Async version of register_template."""
        async with self._templates_lock:
            self._templates[template.name] = template

            if self._enable_logging:
                logger.info(f"Context template registered: {template.name}")

    def unregister_template(self, template_name: str) -> bool:
        """
        Unregister a context template.

        Args:
            template_name: Name of the template to unregister.

        Returns:
            True if template was unregistered, False otherwise.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context_manager.unregister_template("api_request")
            True
        """
        return asyncio.run(self._unregister_template_async(template_name))

    async def _unregister_template_async(self, template_name: str) -> bool:
        """Async version of unregister_template."""
        async with self._templates_lock:
            if template_name in self._templates:
                del self._templates[template_name]

                if self._enable_logging:
                    logger.info(f"Context template unregistered: {template_name}")
                return True
            return False

    def get_template(self, template_name: str) -> Optional[ContextTemplate]:
        """
        Get a context template.

        Args:
            template_name: Name of the template.

        Returns:
            ContextTemplate if found, None otherwise.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> template = context_manager.get_template("api_request")
        """
        return self._templates.get(template_name)

    def create_from_template(
        self,
        template_name: str,
        runtime_id: str = "",
        **kwargs,
    ) -> Context:
        """
        Create a context from a template.

        Args:
            template_name: Name of the template.
            runtime_id: ID of the runtime creating the context.
            **kwargs: Additional context attributes.

        Returns:
            New context.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context = context_manager.create_from_template(
            ...     "api_request",
            ...     runtime_id="api_runtime",
            ...     request_id="req-123"
            ... )
        """
        template = self.get_template(template_name)
        if template is None:
            raise ValueError(f"Template not found: {template_name}")

        # Merge template defaults with provided values
        values = {**template.default_values, **kwargs.get("values", {})}
        metadata = {**template.default_metadata, **kwargs.get("metadata", {})}

        return self.create(
            runtime_id=runtime_id,
            correlation_id=kwargs.get("correlation_id"),
            conversation_id=kwargs.get("conversation_id"),
            request_id=kwargs.get("request_id"),
            user_id=kwargs.get("user_id"),
            session_id=kwargs.get("session_id"),
            values=values,
            metadata=metadata,
            ttl=kwargs.get("ttl", template.ttl),
        )

    def on_create(
        self, callback: Callable[[Context], None]
    ) -> None:
        """
        Register a callback for context creation.

        Args:
            callback: Callback function to call when a context is created.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> def on_create(context):
            ...     print(f"Context created: {context.context_id}")
            >>> context_manager.on_create(on_create)
        """
        self._on_create.append(callback)

    def on_destroy(
        self, callback: Callable[[Context], None]
    ) -> None:
        """
        Register a callback for context destruction.

        Args:
            callback: Callback function to call when a context is destroyed.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> def on_destroy(context):
            ...     print(f"Context destroyed: {context.context_id}")
            >>> context_manager.on_destroy(on_destroy)
        """
        self._on_destroy.append(callback)

    def propagate_to_message(
        self, message: "Message", context: Optional[Context] = None
    ) -> "Message":
        """
        Propagate context to a message.

        Args:
            message: Message to propagate context to.
            context: Context to propagate (uses current if not provided).

        Returns:
            Message with context propagated.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> from tangku_agentos.runtime_communication.models.messages import Message
            >>> message = Message()
            >>> context = context_manager.create()
            >>> message = context_manager.propagate_to_message(message, context)
        """
        if context is None:
            context = self.get_current()

        if context is None:
            return message

        # Set context values in message headers
        if context.correlation_id:
            message.correlation_id = context.correlation_id
        if context.conversation_id:
            message.conversation_id = context.conversation_id
        if context.request_id:
            message.headers["X-Request-ID"] = context.request_id
        if context.runtime_id:
            message.headers["X-Runtime-ID"] = context.runtime_id
        if context.user_id:
            message.headers["X-User-ID"] = context.user_id
        if context.session_id:
            message.headers["X-Session-ID"] = context.session_id

        # Add context values to message metadata
        for key, value in context.values.items():
            message.metadata[f"context.{key}"] = value

        return message

    def extract_from_message(self, message: "Message") -> Optional[Context]:
        """
        Extract context from a message.

        Args:
            message: Message to extract context from.

        Returns:
            Context extracted from the message or None.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> from tangku_agentos.runtime_communication.models.messages import Message
            >>> message = Message(
            ...     correlation_id="corr-123",
            ...     headers={"X-Request-ID": "req-123"}
            ... )
            >>> context = context_manager.extract_from_message(message)
        """
        # Extract from message fields
        context_data: Dict[str, Any] = {
            "correlation_id": message.correlation_id,
            "conversation_id": message.conversation_id,
            "request_id": message.headers.get("X-Request-ID"),
            "runtime_id": message.sender_id,
            "user_id": message.headers.get("X-User-ID"),
            "session_id": message.headers.get("X-Session-ID"),
        }

        # Extract context values from metadata
        values = {}
        for key, value in message.metadata.items():
            if key.startswith("context."):
                values[key[8:]] = value  # Remove "context." prefix

        if not any(context_data.values()):
            return None

        return Context(
            correlation_id=context_data["correlation_id"],
            conversation_id=context_data["conversation_id"],
            request_id=context_data["request_id"],
            runtime_id=context_data["runtime_id"],
            user_id=context_data["user_id"],
            session_id=context_data["session_id"],
            values=values,
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get context manager metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> metrics = context_manager.get_metrics()
            >>> metrics["contexts_created"]
            0
        """
        return {
            **self._metrics,
            "contexts_count": len(self._contexts),
            "templates_count": len(self._templates),
        }

    def clear(self) -> int:
        """
        Clear all contexts.

        Returns:
            Number of contexts cleared.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> count = context_manager.clear()
        """
        count = len(self._contexts)
        self._contexts.clear()
        self._current_context = None
        self._metrics = {
            "contexts_created": 0,
            "contexts_destroyed": 0,
            "contexts_active": 0,
            "contexts_expired": 0,
            "context_queries": 0,
        }
        return count

    def shutdown(self) -> None:
        """
        Shutdown the context manager.

        Example:
            >>> context_manager = RuntimeContextManager()
            >>> context_manager.shutdown()
        """
        self.clear()
        self._templates.clear()
        self._on_create.clear()
        self._on_destroy.clear()

        logger.info("Runtime context manager shutdown complete")

    def __repr__(self) -> str:
        """Return string representation of the context manager."""
        return (
            f"RuntimeContextManager("
            f"contexts={len(self._contexts)}, "
            f"active={self._metrics['contexts_active']}, "
            f"templates={len(self._templates)})"
        )
