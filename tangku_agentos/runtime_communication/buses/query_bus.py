"""
Runtime Communication Framework - Query Bus Implementation

The QueryBus provides a specialized message bus for query-based communication
patterns. It supports:
- Single recipient queries
- Request/response semantics
- Query validation and authorization
- Result caching (optional)
- Error propagation
- Timeout handling

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    Any,
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
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        MessageType,
        MessagePriority,
        Query,
        Response,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IQueryBus,
        IQueryHandler,
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class QueryRegistration:
    """
    Represents a registered query handler.

    Attributes:
        query_type: Type of query this handler processes.
        handler: Handler function for the query.
        priority: Handler priority (higher = called first).
        active: Whether the handler is active.
        execution_count: Number of times this handler has been called.
        error_count: Number of errors from this handler.
        cache_enabled: Whether caching is enabled for this handler.
        cache_ttl: Cache time-to-live in seconds.
        registered_at: When the handler was registered.
    """

    query_type: str
    handler: "IQueryHandler[Query, Any]"
    priority: int = 0
    active: bool = True
    execution_count: int = 0
    error_count: int = 0
    cache_enabled: bool = False
    cache_ttl: float = 300.0  # 5 minutes
    registered_at: datetime = field(default_factory=datetime.utcnow)


class QueryBus:
    """
    Specialized message bus for query-based communication patterns.

    The QueryBus implements the query/response pattern where queries are sent
    to a single recipient and expect a response containing the requested data.
    It supports:
    - Single recipient queries
    - Request/response semantics
    - Query validation and authorization
    - Result caching (optional)
    - Error propagation
    - Timeout handling

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.buses.query_bus import QueryBus
        >>> from tangku_agentos.runtime_communication.models.messages import Query, MessageType
        >>> 
        >>> bus = QueryBus()
        >>> 
        >>> # Register a query handler
        >>> class GetDataQueryHandler:
        ...     async def handle_query(self, query: Query) -> dict:
        ...         return {"data": "value", "id": query.payload["id"]}
        >>> 
        >>> handler = GetDataQueryHandler()
        >>> bus.register_handler("get.data", handler)
        >>> 
        >>> # Ask a query
        >>> query = Query(
        ...     message_type=MessageType.QUERY,
        ...     sender_id="client",
        ...     query_type="get.data",
        ...     payload={"id": "123"}
        ... )
        >>> result = asyncio.run(bus.ask(query))

    Attributes:
        default_timeout: Default timeout for query execution in seconds.
        max_retries: Maximum number of retry attempts for failed queries.
        cache_enabled: Whether caching is enabled by default.
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        max_retries: int = 3,
        cache_enabled: bool = False,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the query bus.

        Args:
            default_timeout: Default timeout for query execution in seconds.
            max_retries: Maximum number of retry attempts for failed queries.
            cache_enabled: Whether caching is enabled by default.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Query handlers: query_type -> QueryRegistration
        self._handlers: Dict[str, QueryRegistration] = {}
        self._handlers_lock = asyncio.Lock()

        # Query history
        self._query_history: List["Query"] = []
        self._query_history_lock = asyncio.Lock()
        self._max_query_history = 10000

        # Query cache: cache_key -> (result, expiry_time)
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._cache_lock = asyncio.Lock()

        # Configuration
        self._default_timeout = default_timeout
        self._max_retries = max_retries
        self._cache_enabled = cache_enabled

        # Metrics
        self._metrics: Dict[str, Any] = {
            "queries_asked": 0,
            "queries_answered": 0,
            "queries_failed": 0,
            "queries_timed_out": 0,
            "queries_retried": 0,
            "queries_cached": 0,
            "handlers_registered": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"QueryBus initialized with timeout={default_timeout}, "
            f"max_retries={max_retries}, cache_enabled={cache_enabled}"
        )

    async def ask(self, query: "Query") -> Any:
        """
        Ask a query and get a response.

        This is the main method for asking queries. The query will be
        routed to the appropriate handler based on its query_type.

        Args:
            query: Query to ask.

        Returns:
            Result from query execution.

        Raises:
            MessageValidationError: If query validation fails.
            MessageDeliveryError: If query cannot be delivered.
            MessageTimeoutError: If query execution times out.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Query, MessageType
            >>> 
            >>> bus = QueryBus()
            >>> query = Query(
            ...     message_type=MessageType.QUERY,
            ...     sender_id="client",
            ...     query_type="get.data",
            ...     payload={"id": "123"}
            ... )
            >>> result = asyncio.run(bus.ask(query))
        """
        # Validate query
        self._validate_query(query)

        # Set query timestamp if not set
        if query.created_at is None:
            query.created_at = datetime.utcnow()

        # Set default timeout if not set
        if query.timeout <= 0:
            query.timeout = self._default_timeout

        # Update metrics
        async with self._metrics_lock:
            self._metrics["queries_asked"] += 1

        # Record query in history
        await self._record_query(query)

        # Check cache
        cache_key = self._get_cache_key(query)
        if self._cache_enabled:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                async with self._metrics_lock:
                    self._metrics["queries_cached"] += 1
                return cached_result

        # Find handler for this query type
        handler = await self._get_handler(query.query_type)

        if handler is None:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            error_msg = f"No handler registered for query type: {query.query_type}"
            logger.error(error_msg)

            async with self._metrics_lock:
                self._metrics["queries_failed"] += 1

            raise MessageDeliveryError(
                error_msg,
                message_id=query.message_id,
                recipient_id=query.query_type,
            )

        # Execute query with retry logic
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_handler(handler, query),
                    timeout=query.timeout,
                )

                # Cache result if caching is enabled for this handler
                if handler.cache_enabled:
                    await self._cache_result(cache_key, result, handler.cache_ttl)

                async with self._metrics_lock:
                    self._metrics["queries_answered"] += 1

                return result

            except asyncio.TimeoutError as e:
                last_error = e
                async with self._metrics_lock:
                    self._metrics["queries_timed_out"] += 1

                if attempt < self._max_retries:
                    if self._enable_logging:
                        logger.warning(
                            f"Query {query.message_id} timed out, "
                            f"attempt {attempt + 1}/{self._max_retries + 1}"
                        )
                    continue
                else:
                    from tangku_agentos.runtime_communication.models.exceptions import (
                        MessageTimeoutError,
                    )

                    raise MessageTimeoutError(
                        f"Query {query.message_id} timed out after "
                        f"{self._max_retries + 1} attempts",
                        message_id=query.message_id,
                        operation="query_execution",
                        timeout=query.timeout,
                    ) from last_error

            except Exception as e:
                last_error = e
                async with self._metrics_lock:
                    self._metrics["queries_failed"] += 1

                if attempt < self._max_retries:
                    if self._enable_logging:
                        logger.warning(
                            f"Query {query.message_id} failed, "
                            f"attempt {attempt + 1}/{self._max_retries + 1}: {e}"
                        )
                    continue
                else:
                    from tangku_agentos.runtime_communication.models.exceptions import (
                        MessageDeliveryError,
                    )

                    raise MessageDeliveryError(
                        f"Query {query.message_id} failed after "
                        f"{self._max_retries + 1} attempts: {e}",
                        message_id=query.message_id,
                        recipient_id=query.query_type,
                        last_error=str(e),
                    ) from last_error

        # This should never be reached
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageDeliveryError,
        )

        raise MessageDeliveryError(
            f"Query {query.message_id} failed",
            message_id=query.message_id,
            recipient_id=query.query_type,
        )

    def register_handler(
        self,
        query_type: str,
        handler: "IQueryHandler[Query, Any]",
        priority: int = 0,
        cache_enabled: Optional[bool] = None,
        cache_ttl: Optional[float] = None,
    ) -> None:
        """
        Register a query handler.

        Args:
            query_type: Type of query to handle.
            handler: Handler for the query type.
            priority: Handler priority (higher = called first).
            cache_enabled: Whether caching is enabled for this handler.
            cache_ttl: Cache time-to-live in seconds.

        Example:
            >>> class GetDataQueryHandler:
            ...     async def handle_query(self, query: Query) -> dict:
            ...         return {"data": "value"}
            >>> 
            >>> bus = QueryBus()
            >>> handler = GetDataQueryHandler()
            >>> bus.register_handler("get.data", handler, cache_enabled=True)
        """
        asyncio.run(
            self._register_handler_async(
                query_type, handler, priority, cache_enabled, cache_ttl
            )
        )

    async def _register_handler_async(
        self,
        query_type: str,
        handler: "IQueryHandler[Query, Any]",
        priority: int = 0,
        cache_enabled: Optional[bool] = None,
        cache_ttl: Optional[float] = None,
    ) -> None:
        """Async version of register_handler."""
        registration = QueryRegistration(
            query_type=query_type,
            handler=handler,
            priority=priority,
            cache_enabled=cache_enabled if cache_enabled is not None else self._cache_enabled,
            cache_ttl=cache_ttl if cache_ttl is not None else 300.0,
        )

        async with self._handlers_lock:
            self._handlers[query_type] = registration

            async with self._metrics_lock:
                self._metrics["handlers_registered"] += 1

            if self._enable_logging:
                logger.info(
                    f"Query handler registered for '{query_type}': "
                    f"{handler.__class__.__name__}"
                )

    def unregister_handler(self, query_type: str) -> bool:
        """
        Unregister a query handler.

        Args:
            query_type: Type of query.

        Returns:
            True if handler was removed, False otherwise.

        Example:
            >>> bus = QueryBus()
            >>> bus.register_handler("get.data", handler)
            >>> bus.unregister_handler("get.data")
            True
        """
        return asyncio.run(self._unregister_handler_async(query_type))

    async def _unregister_handler_async(self, query_type: str) -> bool:
        """Async version of unregister_handler."""
        async with self._handlers_lock:
            if query_type in self._handlers:
                del self._handlers[query_type]

                async with self._metrics_lock:
                    self._metrics["handlers_registered"] -= 1

                if self._enable_logging:
                    logger.info(f"Query handler unregistered: {query_type}")
                return True
            return False

    def has_handler(self, query_type: str) -> bool:
        """
        Check if a handler is registered for a query type.

        Args:
            query_type: Type of query to check.

        Returns:
            True if handler is registered, False otherwise.

        Example:
            >>> bus = QueryBus()
            >>> bus.register_handler("get.data", handler)
            >>> bus.has_handler("get.data")
            True
        """
        return query_type in self._handlers

    def list_handlers(self) -> List[str]:
        """
        List all registered query types.

        Returns:
            List of query types with registered handlers.

        Example:
            >>> bus = QueryBus()
            >>> bus.register_handler("get.data", handler)
            >>> bus.list_handlers()
            ['get.data']
        """
        return list(self._handlers.keys())

    def get_query_history(
        self,
        query_type: Optional[str] = None,
        limit: int = 100,
    ) -> List["Query"]:
        """
        Retrieve query history with optional filtering.

        Args:
            query_type: Filter by query type (optional).
            limit: Maximum queries to return.

        Returns:
            List of queries.

        Example:
            >>> bus = QueryBus()
            >>> # Ask some queries
            >>> history = bus.get_query_history(limit=10)
        """
        queries = list(self._query_history)

        if query_type is not None:
            queries = [q for q in queries if q.query_type == query_type]

        return queries[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get query bus metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> bus = QueryBus()
            >>> metrics = bus.get_metrics()
            >>> metrics["queries_asked"]
            0
        """
        return {
            **self._metrics,
            "query_history_size": len(self._query_history),
            "handlers_count": len(self._handlers),
            "cache_size": len(self._cache),
        }

    def clear_history(self) -> int:
        """
        Clear query history.

        Returns:
            Count of queries cleared.

        Example:
            >>> bus = QueryBus()
            >>> count = bus.clear_history()
        """
        count = len(self._query_history)
        self._query_history.clear()
        return count

    def clear_cache(self) -> int:
        """
        Clear query cache.

        Returns:
            Count of cached items cleared.

        Example:
            >>> bus = QueryBus()
            >>> count = bus.clear_cache()
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def shutdown(self) -> None:
        """
        Shutdown query bus.

        Cleans up resources and stops all processing.

        Example:
            >>> bus = QueryBus()
            >>> bus.shutdown()
        """
        self._query_history.clear()
        self._cache.clear()
        self._handlers.clear()
        self._metrics.clear()

        logger.info("Query bus shutdown complete")

    async def _get_handler(self, query_type: str) -> Optional[QueryRegistration]:
        """
        Get the handler for a query type.

        Args:
            query_type: Type of query.

        Returns:
            QueryRegistration if found, None otherwise.
        """
        async with self._handlers_lock:
            return self._handlers.get(query_type)

    async def _execute_handler(
        self,
        registration: QueryRegistration,
        query: "Query",
    ) -> Any:
        """
        Execute a query handler.

        Args:
            registration: Handler registration.
            query: Query to execute.

        Returns:
            Result from handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not registration.active:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            raise MessageDeliveryError(
                f"Handler for query type '{registration.query_type}' is inactive",
                message_id=query.message_id,
                recipient_id=registration.query_type,
            )

        registration.execution_count += 1

        try:
            return await registration.handler.handle_query(query)
        except Exception as e:
            registration.error_count += 1
            logger.error(
                f"Error executing query {query.message_id} "
                f"with handler {registration.handler.__class__.__name__}: {e}"
            )
            raise

    async def _record_query(self, query: "Query") -> None:
        """
        Store query in history.

        Args:
            query: Query to store.
        """
        async with self._query_history_lock:
            self._query_history.append(query)
            if len(self._query_history) > self._max_query_history:
                self._query_history.pop(0)

    def _get_cache_key(self, query: "Query") -> str:
        """
        Generate a cache key for a query.

        Args:
            query: Query to generate key for.

        Returns:
            Cache key string.
        """
        # Simple cache key based on query type and payload
        # In production, this could be more sophisticated
        import json

        payload_str = json.dumps(query.payload, sort_keys=True) if query.payload else ""
        return f"{query.query_type}:{payload_str}"

    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get a cached result.

        Args:
            cache_key: Cache key to look up.

        Returns:
            Cached result if found and not expired, None otherwise.
        """
        async with self._cache_lock:
            if cache_key in self._cache:
                result, expiry_time = self._cache[cache_key]
                if datetime.utcnow() < expiry_time:
                    return result
                else:
                    # Expired, remove from cache
                    del self._cache[cache_key]
            return None

    async def _cache_result(
        self, cache_key: str, result: Any, ttl: float
    ) -> None:
        """
        Cache a result.

        Args:
            cache_key: Cache key to store under.
            result: Result to cache.
            ttl: Time-to-live in seconds.
        """
        async with self._cache_lock:
            expiry_time = datetime.utcnow() + timedelta(seconds=ttl)
            self._cache[cache_key] = (result, expiry_time)

    def _validate_query(self, query: "Query") -> None:
        """
        Validate a query before asking.

        Args:
            query: Query to validate.

        Raises:
            MessageValidationError: If query is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not query.sender_id:
            raise MessageValidationError(
                "Query sender_id is required",
                message_id=query.message_id,
                validation_errors=["sender_id is required"],
            )

        if not query.query_type:
            raise MessageValidationError(
                "Query query_type is required",
                message_id=query.message_id,
                validation_errors=["query_type is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the query bus."""
        return (
            f"QueryBus("
            f"handlers={len(self._handlers)}, "
            f"history={len(self._query_history)}, "
            f"cache={len(self._cache)})"
        )
