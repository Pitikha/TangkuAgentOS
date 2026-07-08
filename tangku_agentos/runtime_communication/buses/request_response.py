"""
Runtime Communication Framework - Request/Response Bus Implementation

The RequestResponseBus provides a specialized message bus for request/response
communication patterns. It supports:
- Request/response correlation
- Synchronous and asynchronous responses
- Response matching
- Timeout handling
- Error propagation

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
        Command,
        Response,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IRequestResponseBus,
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class RequestHandler:
    """
    Represents a registered request handler.

    Attributes:
        request_type: Type of request this handler processes.
        handler: Handler function for the request.
        priority: Handler priority (higher = called first).
        active: Whether the handler is active.
        execution_count: Number of times this handler has been called.
        error_count: Number of errors from this handler.
        registered_at: When the handler was registered.
    """

    request_type: str
    handler: Callable[["Message"], Any]
    priority: int = 0
    active: bool = True
    execution_count: int = 0
    error_count: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)


class RequestResponseBus:
    """
    Specialized message bus for request/response communication patterns.

    The RequestResponseBus implements the request/response pattern where
    requests are sent and responses are correlated with the original request.
    It supports:
    - Request/response correlation via correlation IDs
    - Synchronous and asynchronous responses
    - Response matching
    - Timeout handling
    - Error propagation

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.buses.request_response import RequestResponseBus
        >>> from tangku_agentos.runtime_communication.models.messages import Message, MessageType
        >>> 
        >>> bus = RequestResponseBus()
        >>> 
        >>> # Register a request handler
        >>> async def handle_get_data(request: Message) -> Message:
        ...     from tangku_agentos.runtime_communication.models.messages import Response
        ...     return Response.success(
        ...         request_id=request.message_id,
        ...         result={"data": "value"}
        ...     )
        >>> 
        >>> bus.register_request_handler("get.data", handle_get_data)
        >>> 
        >>> # Send a request
        >>> request = Message(
        ...     message_type=MessageType.QUERY,
        ...     sender_id="client",
        ...     payload={"id": "123"},
        ...     correlation_id="req-123"
        ... )
        >>> response = asyncio.run(bus.request(request, timeout=5.0))

    Attributes:
        default_timeout: Default timeout for requests in seconds.
        max_pending_requests: Maximum number of pending requests to track.
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        max_pending_requests: int = 10000,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the request/response bus.

        Args:
            default_timeout: Default timeout for requests in seconds.
            max_pending_requests: Maximum number of pending requests to track.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Request handlers: request_type -> RequestHandler
        self._handlers: Dict[str, RequestHandler] = {}
        self._handlers_lock = asyncio.Lock()

        # Pending requests: correlation_id -> asyncio.Future
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._pending_requests_lock = asyncio.Lock()
        self._max_pending_requests = max_pending_requests

        # Request history
        self._request_history: List["Message"] = []
        self._request_history_lock = asyncio.Lock()
        self._max_request_history = 10000

        # Response history
        self._response_history: List["Message"] = []
        self._response_history_lock = asyncio.Lock()
        self._max_response_history = 10000

        # Configuration
        self._default_timeout = default_timeout

        # Metrics
        self._metrics: Dict[str, Any] = {
            "requests_sent": 0,
            "requests_received": 0,
            "responses_sent": 0,
            "responses_received": 0,
            "requests_timed_out": 0,
            "requests_failed": 0,
            "handlers_registered": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"RequestResponseBus initialized with timeout={default_timeout}, "
            f"max_pending={max_pending_requests}"
        )

    async def request(
        self,
        request: "Message",
        timeout: Optional[float] = None,
    ) -> "Message":
        """
        Send a request and wait for a response.

        This is the main method for sending requests. The request will be
        routed to the appropriate handler, and this method will wait for
        the corresponding response.

        Args:
            request: Request message to send.
            timeout: Timeout for response in seconds.

        Returns:
            Response message.

        Raises:
            MessageTimeoutError: If response times out.
            MessageDeliveryError: If request cannot be delivered.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Message, MessageType
            >>> 
            >>> bus = RequestResponseBus()
            >>> request = Message(
            ...     message_type=MessageType.QUERY,
            ...     sender_id="client",
            ...     payload={"id": "123"},
            ...     correlation_id="req-123"
            ... )
            >>> response = asyncio.run(bus.request(request, timeout=5.0))
        """
        # Validate request
        self._validate_request(request)

        # Set correlation ID if not set
        if request.correlation_id is None:
            request.correlation_id = str(uuid.uuid4())

        # Set reply_to if not set
        if request.reply_to is None:
            request.reply_to = request.message_id

        # Set timestamp if not set
        if request.created_at is None:
            request.created_at = datetime.utcnow()

        # Set default timeout if not set
        if timeout is None:
            timeout = self._default_timeout

        # Update metrics
        async with self._metrics_lock:
            self._metrics["requests_sent"] += 1

        # Record request in history
        await self._record_request(request)

        # Create future for response
        response_future: asyncio.Future = asyncio.Future()

        # Store pending request
        async with self._pending_requests_lock:
            # Clean up old pending requests if at capacity
            if len(self._pending_requests) >= self._max_pending_requests:
                self._cleanup_pending_requests()

            self._pending_requests[request.correlation_id] = response_future

        try:
            # Route the request
            await self._route_request(request)

            # Wait for response
            response = await asyncio.wait_for(
                response_future, timeout=timeout
            )

            # Update metrics
            async with self._metrics_lock:
                self._metrics["responses_received"] += 1

            # Record response in history
            await self._record_response(response)

            return response

        except asyncio.TimeoutError:
            async with self._metrics_lock:
                self._metrics["requests_timed_out"] += 1

            # Clean up pending request
            async with self._pending_requests_lock:
                if request.correlation_id in self._pending_requests:
                    del self._pending_requests[request.correlation_id]

            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageTimeoutError,
            )

            raise MessageTimeoutError(
                f"Request {request.correlation_id} timed out after {timeout}s",
                message_id=request.message_id,
                operation="request_response",
                timeout=timeout,
            )
        except Exception as e:
            async with self._metrics_lock:
                self._metrics["requests_failed"] += 1

            # Clean up pending request
            async with self._pending_requests_lock:
                if request.correlation_id in self._pending_requests:
                    del self._pending_requests[request.correlation_id]

            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            raise MessageDeliveryError(
                f"Request {request.correlation_id} failed: {e}",
                message_id=request.message_id,
                last_error=str(e),
            ) from e

    async def reply(
        self,
        response: "Message",
        request_id: Optional[str] = None,
    ) -> None:
        """
        Send a reply to a request.

        This method is used by request handlers to send responses back to
        the original requester.

        Args:
            response: Response message to send.
            request_id: ID of the original request (optional, uses reply_to if not provided).

        Raises:
            MessageDeliveryError: If the original request is not found.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Response
            >>> 
            >>> bus = RequestResponseBus()
            >>> response = Response.success(
            ...     request_id="req-123",
            ...     result={"data": "value"}
            ... )
            >>> asyncio.run(bus.reply(response))
        """
        # Validate response
        self._validate_response(response)

        # Set timestamp if not set
        if response.created_at is None:
            response.created_at = datetime.utcnow()

        # Determine request ID
        request_id = request_id or response.reply_to
        if request_id is None:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            raise MessageDeliveryError(
                "Response has no reply_to or request_id",
                message_id=response.message_id,
            )

        # Update metrics
        async with self._metrics_lock:
            self._metrics["responses_sent"] += 1

        # Record response in history
        await self._record_response(response)

        # Find and complete the pending request
        async with self._pending_requests_lock:
            if request_id in self._pending_requests:
                future = self._pending_requests.pop(request_id)
                if not future.done():
                    future.set_result(response)
            else:
                if self._enable_logging:
                    logger.warning(
                        f"No pending request found for reply: {request_id}"
                    )

    def register_request_handler(
        self,
        request_type: str,
        handler: Callable[["Message"], Any],
        priority: int = 0,
    ) -> None:
        """
        Register a handler for a request type.

        Args:
            request_type: Type of request to handle.
            handler: Handler function for the request type.
            priority: Handler priority (higher = called first).

        Example:
            >>> async def handle_get_data(request: Message) -> Message:
            ...     from tangku_agentos.runtime_communication.models.messages import Response
            ...     return Response.success(
            ...         request_id=request.message_id,
            ...         result={"data": "value"}
            ...     )
            >>> 
            >>> bus = RequestResponseBus()
            >>> bus.register_request_handler("get.data", handle_get_data)
        """
        asyncio.run(
            self._register_request_handler_async(request_type, handler, priority)
        )

    async def _register_request_handler_async(
        self,
        request_type: str,
        handler: Callable[["Message"], Any],
        priority: int = 0,
    ) -> None:
        """Async version of register_request_handler."""
        registration = RequestHandler(
            request_type=request_type,
            handler=handler,
            priority=priority,
        )

        async with self._handlers_lock:
            self._handlers[request_type] = registration

            async with self._metrics_lock:
                self._metrics["handlers_registered"] += 1

            if self._enable_logging:
                logger.info(
                    f"Request handler registered for '{request_type}': "
                    f"{handler.__name__}"
                )

    def unregister_request_handler(self, request_type: str) -> bool:
        """
        Unregister a request handler.

        Args:
            request_type: Type of request.

        Returns:
            True if handler was removed, False otherwise.

        Example:
            >>> bus = RequestResponseBus()
            >>> bus.register_request_handler("get.data", handler)
            >>> bus.unregister_request_handler("get.data")
            True
        """
        return asyncio.run(self._unregister_request_handler_async(request_type))

    async def _unregister_request_handler_async(
        self, request_type: str
    ) -> bool:
        """Async version of unregister_request_handler."""
        async with self._handlers_lock:
            if request_type in self._handlers:
                del self._handlers[request_type]

                async with self._metrics_lock:
                    self._metrics["handlers_registered"] -= 1

                if self._enable_logging:
                    logger.info(f"Request handler unregistered: {request_type}")
                return True
            return False

    def has_handler(self, request_type: str) -> bool:
        """
        Check if a handler is registered for a request type.

        Args:
            request_type: Type of request to check.

        Returns:
            True if handler is registered, False otherwise.

        Example:
            >>> bus = RequestResponseBus()
            >>> bus.register_request_handler("get.data", handler)
            >>> bus.has_handler("get.data")
            True
        """
        return request_type in self._handlers

    def list_handlers(self) -> List[str]:
        """
        List all registered request types.

        Returns:
            List of request types with registered handlers.

        Example:
            >>> bus = RequestResponseBus()
            >>> bus.register_request_handler("get.data", handler)
            >>> bus.list_handlers()
            ['get.data']
        """
        return list(self._handlers.keys())

    def get_request_history(
        self,
        request_type: Optional[str] = None,
        limit: int = 100,
    ) -> List["Message"]:
        """
        Retrieve request history with optional filtering.

        Args:
            request_type: Filter by request type (optional).
            limit: Maximum requests to return.

        Returns:
            List of requests.

        Example:
            >>> bus = RequestResponseBus()
            >>> # Send some requests
            >>> history = bus.get_request_history(limit=10)
        """
        requests = list(self._request_history)

        if request_type is not None:
            requests = [
                r
                for r in requests
                if r.message_type.name == request_type
            ]

        return requests[-limit:]

    def get_response_history(
        self,
        limit: int = 100,
    ) -> List["Message"]:
        """
        Retrieve response history.

        Args:
            limit: Maximum responses to return.

        Returns:
            List of responses.

        Example:
            >>> bus = RequestResponseBus()
            >>> # Receive some responses
            >>> history = bus.get_response_history(limit=10)
        """
        return list(self._response_history)[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get request/response bus metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> bus = RequestResponseBus()
            >>> metrics = bus.get_metrics()
            >>> metrics["requests_sent"]
            0
        """
        return {
            **self._metrics,
            "request_history_size": len(self._request_history),
            "response_history_size": len(self._response_history),
            "pending_requests": len(self._pending_requests),
            "handlers_count": len(self._handlers),
        }

    def clear_history(self) -> int:
        """
        Clear request and response history.

        Returns:
            Count of items cleared.

        Example:
            >>> bus = RequestResponseBus()
            >>> count = bus.clear_history()
        """
        count = len(self._request_history) + len(self._response_history)
        self._request_history.clear()
        self._response_history.clear()
        return count

    def clear_pending(self) -> int:
        """
        Clear pending requests.

        Returns:
            Count of pending requests cleared.

        Example:
            >>> bus = RequestResponseBus()
            >>> count = bus.clear_pending()
        """
        count = len(self._pending_requests)
        self._pending_requests.clear()
        return count

    def shutdown(self) -> None:
        """
        Shutdown request/response bus.

        Cleans up resources and stops all processing.

        Example:
            >>> bus = RequestResponseBus()
            >>> bus.shutdown()
        """
        self._request_history.clear()
        self._response_history.clear()
        self._pending_requests.clear()
        self._handlers.clear()
        self._metrics.clear()

        logger.info("Request/Response bus shutdown complete")

    async def _route_request(self, request: "Message") -> None:
        """
        Route a request to the appropriate handler.

        Args:
            request: Request to route.
        """
        # Find handler for this request type
        request_type = request.message_type.name
        handler = await self._get_handler(request_type)

        if handler is None:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            error_msg = f"No handler registered for request type: {request_type}"
            logger.error(error_msg)

            # Try to send error response
            async with self._pending_requests_lock:
                if request.correlation_id in self._pending_requests:
                    future = self._pending_requests.pop(request.correlation_id)
                    if not future.done():
                        from tangku_agentos.runtime_communication.models.messages import (
                            Response,
                        )

                        error_response = Response.error(
                            request_id=request.correlation_id,
                            error=error_msg,
                        )
                        future.set_result(error_response)

            async with self._metrics_lock:
                self._metrics["requests_failed"] += 1

            return

        # Update metrics
        async with self._metrics_lock:
            self._metrics["requests_received"] += 1

        # Execute handler
        try:
            result = await handler.handler(request)

            # If result is a Message, send it as reply
            if isinstance(result, Message):
                await self.reply(result, request.correlation_id)
            else:
                # Wrap result in a Response message
                from tangku_agentos.runtime_communication.models.messages import (
                    Response,
                )

                response = Response.success(
                    request_id=request.correlation_id,
                    result=result,
                )
                await self.reply(response, request.correlation_id)

        except Exception as e:
            logger.error(
                f"Error handling request {request.correlation_id}: {e}"
            )

            # Try to send error response
            async with self._pending_requests_lock:
                if request.correlation_id in self._pending_requests:
                    future = self._pending_requests.pop(request.correlation_id)
                    if not future.done():
                        from tangku_agentos.runtime_communication.models.messages import (
                            Response,
                        )

                        error_response = Response.error(
                            request_id=request.correlation_id,
                            error=str(e),
                        )
                        future.set_result(error_response)

            async with self._metrics_lock:
                self._metrics["requests_failed"] += 1

    async def _get_handler(self, request_type: str) -> Optional[RequestHandler]:
        """
        Get the handler for a request type.

        Args:
            request_type: Type of request.

        Returns:
            RequestHandler if found, None otherwise.
        """
        async with self._handlers_lock:
            return self._handlers.get(request_type)

    async def _record_request(self, request: "Message") -> None:
        """
        Store request in history.

        Args:
            request: Request to store.
        """
        async with self._request_history_lock:
            self._request_history.append(request)
            if len(self._request_history) > self._max_request_history:
                self._request_history.pop(0)

    async def _record_response(self, response: "Message") -> None:
        """
        Store response in history.

        Args:
            response: Response to store.
        """
        async with self._response_history_lock:
            self._response_history.append(response)
            if len(self._response_history) > self._max_response_history:
                self._response_history.pop(0)

    def _cleanup_pending_requests(self) -> None:
        """
        Clean up old pending requests.

        Removes pending requests that have been waiting too long.
        """
        import time

        current_time = time.time()
        to_remove = []

        for correlation_id, future in self._pending_requests.items():
            # Check if future has been waiting too long
            # This is a simple cleanup; in production, you might want more sophisticated logic
            if future.done():
                to_remove.append(correlation_id)

        for correlation_id in to_remove:
            del self._pending_requests[correlation_id]

    def _validate_request(self, request: "Message") -> None:
        """
        Validate a request before sending.

        Args:
            request: Request to validate.

        Raises:
            MessageValidationError: If request is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not request.sender_id:
            raise MessageValidationError(
                "Request sender_id is required",
                message_id=request.message_id,
                validation_errors=["sender_id is required"],
            )

    def _validate_response(self, response: "Message") -> None:
        """
        Validate a response before sending.

        Args:
            response: Response to validate.

        Raises:
            MessageValidationError: If response is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not response.sender_id:
            raise MessageValidationError(
                "Response sender_id is required",
                message_id=response.message_id,
                validation_errors=["sender_id is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the request/response bus."""
        return (
            f"RequestResponseBus("
            f"handlers={len(self._handlers)}, "
            f"pending={len(self._pending_requests)}, "
            f"requests={len(self._request_history)}, "
            f"responses={len(self._response_history)})"
        )
