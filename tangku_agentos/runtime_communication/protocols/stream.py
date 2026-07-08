"""
Runtime Communication Framework - Stream Protocol

The StreamProtocol implements the streaming communication pattern for the
Runtime Communication Framework. It provides:
- Continuous data flow
- Backpressure support
- Chunked delivery
- Stream management
- Flow control

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
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
        StreamMessage,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class StreamContext:
    """
    Context for a stream.

    Attributes:
        stream_id: Unique identifier for the stream.
        source: Source of the stream.
        destination: Destination of the stream.
        created_at: When the stream was created.
        is_active: Whether the stream is active.
        is_paused: Whether the stream is paused.
        backpressure: Whether backpressure is being applied.
        bytes_sent: Number of bytes sent.
        bytes_received: Number of bytes received.
        chunks_sent: Number of chunks sent.
        chunks_received: Number of chunks received.
        metadata: Additional stream metadata.
    """

    stream_id: str
    source: str
    destination: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_paused: bool = False
    backpressure: bool = False
    bytes_sent: int = 0
    bytes_received: int = 0
    chunks_sent: int = 0
    chunks_received: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamSubscription:
    """
    Represents a subscription to a stream.

    Attributes:
        subscription_id: Unique identifier for the subscription.
        stream_id: ID of the stream to subscribe to.
        handler: Handler function to call for stream chunks.
        on_start: Optional handler for stream start.
        on_end: Optional handler for stream end.
        on_error: Optional handler for stream errors.
        priority: Subscription priority (higher = processed first).
        active: Whether the subscription is active.
        chunks_received: Number of chunks received.
        bytes_received: Number of bytes received.
        created_at: When the subscription was created.
    """

    subscription_id: str
    stream_id: str
    handler: "IMessageHandler[StreamMessage]"
    on_start: Optional[Callable[[str], None]] = None
    on_end: Optional[Callable[[str], None]] = None
    on_error: Optional[Callable[[str, Exception], None]] = None
    priority: int = 0
    active: bool = True
    chunks_received: int = 0
    bytes_received: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    async def process(self, chunk: "StreamMessage") -> Any:
        """
        Process a stream chunk with this subscription.

        Args:
            chunk: The stream chunk to process.

        Returns:
            Result from the handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not self.active:
            return None

        self.chunks_received += 1
        self.bytes_received += chunk.chunk_size

        try:
            return await self.handler.handle(chunk)
        except Exception as e:
            if self.on_error is not None:
                try:
                    self.on_error(chunk.stream_id, e)
                except Exception as error_handler_error:
                    logger.error(
                        f"Error in stream error handler: {error_handler_error}"
                    )
            raise


class StreamProtocol:
    """
    Stream protocol implementation.

    The StreamProtocol implements the streaming communication pattern for
    continuous data flow. It provides:
    - Stream creation and management
    - Chunked data delivery
    - Backpressure support
    - Flow control
    - Stream subscription

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.protocols.stream import StreamProtocol
        >>> from tangku_agentos.runtime_communication.models.messages import StreamMessage, MessageType
        >>> 
        >>> protocol = StreamProtocol()
        >>> 
        >>> # Create a stream
        >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
        >>> 
        >>> # Subscribe to the stream
        >>> class MyStreamHandler:
        ...     async def handle(self, chunk: StreamMessage) -> None:
        ...         print(f"Chunk {chunk.sequence_number}: {chunk.payload}")
        >>> 
        >>> handler = MyStreamHandler()
        >>> sub_id = protocol.subscribe(stream_id, handler)
        >>> 
        >>> # Send chunks
        >>> chunk1 = StreamMessage(
        ...     message_type=MessageType.STREAM,
        ...     sender_id="source",
        ...     stream_id=stream_id,
        ...     sequence_number=1,
        ...     is_start=True,
        ...     payload=b"chunk1",
        ...     chunk_size=6
        ... )
        >>> asyncio.run(protocol.send_chunk(chunk1))

    Attributes:
        max_streams: Maximum number of concurrent streams.
        max_chunk_size: Maximum chunk size in bytes.
        backpressure_threshold: Threshold for applying backpressure.
    """

    def __init__(
        self,
        max_streams: int = 1000,
        max_chunk_size: int = 1024 * 1024,  # 1MB
        backpressure_threshold: int = 100,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the stream protocol.

        Args:
            max_streams: Maximum number of concurrent streams.
            max_chunk_size: Maximum chunk size in bytes.
            backpressure_threshold: Threshold for applying backpressure.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Streams: stream_id -> StreamContext
        self._streams: Dict[str, StreamContext] = {}
        self._streams_lock = asyncio.Lock()
        self._max_streams = max_streams

        # Subscriptions: stream_id -> List[StreamSubscription]
        self._subscriptions: Dict[str, List[StreamSubscription]] = defaultdict(list)
        self._subscriptions_lock = asyncio.Lock()

        # Configuration
        self._max_chunk_size = max_chunk_size
        self._backpressure_threshold = backpressure_threshold

        # Metrics
        self._metrics: Dict[str, Any] = {
            "streams_created": 0,
            "streams_ended": 0,
            "streams_paused": 0,
            "streams_resumed": 0,
            "chunks_sent": 0,
            "chunks_delivered": 0,
            "chunks_failed": 0,
            "subscriptions_active": 0,
            "subscriptions_total": 0,
            "backpressure_events": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"StreamProtocol initialized with max_streams={max_streams}, "
            f"max_chunk_size={max_chunk_size}, backpressure_threshold={backpressure_threshold}"
        )

    async def create_stream(
        self,
        source: str,
        destination: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new stream.

        Args:
            source: Source of the stream.
            destination: Destination of the stream.
            metadata: Additional stream metadata.

        Returns:
            Stream ID.

        Raises:
            RuntimeError: If maximum number of streams is reached.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
        """
        async with self._streams_lock:
            if len(self._streams) >= self._max_streams:
                raise RuntimeError(
                    f"Maximum number of streams ({self._max_streams}) reached"
                )

            stream_id = str(uuid.uuid4())
            context = StreamContext(
                stream_id=stream_id,
                source=source,
                destination=destination,
                metadata=metadata or {},
            )

            self._streams[stream_id] = context

            async with self._metrics_lock:
                self._metrics["streams_created"] += 1

            if self._enable_logging:
                logger.info(
                    f"Stream created: {stream_id} ({source} -> {destination})"
                )

            return stream_id

    async def end_stream(
        self,
        stream_id: str,
        error: Optional[Exception] = None,
    ) -> bool:
        """
        End a stream.

        Args:
            stream_id: ID of the stream to end.
            error: Optional error that caused the stream to end.

        Returns:
            True if stream was ended, False otherwise.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> asyncio.run(protocol.end_stream(stream_id))
            True
        """
        async with self._streams_lock:
            if stream_id not in self._streams:
                return False

            context = self._streams[stream_id]
            context.is_active = False

            async with self._metrics_lock:
                self._metrics["streams_ended"] += 1

            if self._enable_logging:
                if error:
                    logger.warning(f"Stream ended with error: {stream_id}: {error}")
                else:
                    logger.info(f"Stream ended: {stream_id}")

            # Notify subscribers of stream end
            await self._notify_stream_end(stream_id, error)

            return True

    async def pause_stream(self, stream_id: str) -> bool:
        """
        Pause a stream.

        Args:
            stream_id: ID of the stream to pause.

        Returns:
            True if stream was paused, False otherwise.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> asyncio.run(protocol.pause_stream(stream_id))
            True
        """
        async with self._streams_lock:
            if stream_id not in self._streams:
                return False

            context = self._streams[stream_id]
            if context.is_paused:
                return False

            context.is_paused = True

            async with self._metrics_lock:
                self._metrics["streams_paused"] += 1

            if self._enable_logging:
                logger.info(f"Stream paused: {stream_id}")

            return True

    async def resume_stream(self, stream_id: str) -> bool:
        """
        Resume a paused stream.

        Args:
            stream_id: ID of the stream to resume.

        Returns:
            True if stream was resumed, False otherwise.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> asyncio.run(protocol.pause_stream(stream_id))
            >>> asyncio.run(protocol.resume_stream(stream_id))
            True
        """
        async with self._streams_lock:
            if stream_id not in self._streams:
                return False

            context = self._streams[stream_id]
            if not context.is_paused:
                return False

            context.is_paused = False

            async with self._metrics_lock:
                self._metrics["streams_resumed"] += 1

            if self._enable_logging:
                logger.info(f"Stream resumed: {stream_id}")

            return True

    async def send_chunk(self, chunk: "StreamMessage") -> int:
        """
        Send a chunk of data for a stream.

        Args:
            chunk: Stream chunk to send.

        Returns:
            Number of subscribers that received the chunk.

        Raises:
            MessageValidationError: If chunk validation fails.
            RuntimeError: If stream is not active or paused.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import StreamMessage, MessageType
            >>> 
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> chunk = StreamMessage(
            ...     message_type=MessageType.STREAM,
            ...     sender_id="source",
            ...     stream_id=stream_id,
            ...     sequence_number=1,
            ...     payload=b"data",
            ...     chunk_size=4
            ... )
            >>> count = asyncio.run(protocol.send_chunk(chunk))
        """
        # Validate chunk
        self._validate_chunk(chunk)

        # Check stream exists and is active
        async with self._streams_lock:
            if chunk.stream_id not in self._streams:
                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageDeliveryError,
                )

                raise MessageDeliveryError(
                    f"Stream not found: {chunk.stream_id}",
                    message_id=chunk.message_id,
                    recipient_id=chunk.stream_id,
                )

            context = self._streams[chunk.stream_id]
            if not context.is_active:
                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageDeliveryError,
                )

                raise MessageDeliveryError(
                    f"Stream is not active: {chunk.stream_id}",
                    message_id=chunk.message_id,
                    recipient_id=chunk.stream_id,
                )

            if context.is_paused:
                # Apply backpressure
                context.backpressure = True
                async with self._metrics_lock:
                    self._metrics["backpressure_events"] += 1

                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageDeliveryError,
                )

                raise MessageDeliveryError(
                    f"Stream is paused: {chunk.stream_id}",
                    message_id=chunk.message_id,
                    recipient_id=chunk.stream_id,
                )

            # Update stream context
            context.chunks_sent += 1
            context.bytes_sent += chunk.chunk_size

        # Set stream ID in chunk if not set
        if chunk.stream_id is None:
            chunk.stream_id = str(uuid.uuid4())

        # Set timestamp if not set
        if chunk.created_at is None:
            chunk.created_at = datetime.utcnow()

        # Update metrics
        async with self._metrics_lock:
            self._metrics["chunks_sent"] += 1

        # Find matching subscriptions
        matching_subscriptions = await self._find_matching_subscriptions(chunk)

        if not matching_subscriptions:
            if self._enable_logging:
                logger.debug(f"No subscribers for stream: {chunk.stream_id}")
            return 0

        # Process chunk with all matching subscriptions
        tasks = []
        for sub in matching_subscriptions:
            task = asyncio.create_task(sub.process(chunk))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update delivered count
        delivered_count = sum(
            1 for r in results if not isinstance(r, Exception)
        )
        async with self._metrics_lock:
            self._metrics["chunks_delivered"] += delivered_count

        # Log errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"Error processing chunk {chunk.message_id} on stream {chunk.stream_id}: {result}"
                )
                async with self._metrics_lock:
                    self._metrics["chunks_failed"] += 1

        return len(matching_subscriptions)

    def subscribe(
        self,
        stream_id: str,
        handler: "IMessageHandler[StreamMessage]",
        on_start: Optional[Callable[[str], None]] = None,
        on_end: Optional[Callable[[str, Optional[Exception]], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
        priority: int = 0,
    ) -> str:
        """
        Subscribe to a stream.

        Args:
            stream_id: ID of the stream to subscribe to.
            handler: Handler to call for stream chunks.
            on_start: Optional handler for stream start.
            on_end: Optional handler for stream end.
            on_error: Optional handler for stream errors.
            priority: Subscription priority (higher = processed first).

        Returns:
            Subscription ID.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> 
            >>> class MyStreamHandler:
            ...     async def handle(self, chunk: StreamMessage) -> None:
            ...         print(f"Chunk: {chunk.payload}")
            >>> 
            >>> handler = MyStreamHandler()
            >>> sub_id = protocol.subscribe(stream_id, handler)
        """
        subscription_id = str(uuid.uuid4())

        subscription = StreamSubscription(
            subscription_id=subscription_id,
            stream_id=stream_id,
            handler=handler,
            on_start=on_start,
            on_end=on_end,
            on_error=on_error,
            priority=priority,
        )

        asyncio.run(self._subscribe_async(subscription))
        return subscription_id

    async def _subscribe_async(self, subscription: StreamSubscription) -> None:
        """Async version of subscribe."""
        async with self._subscriptions_lock:
            self._subscriptions[subscription.stream_id].append(subscription)
            self._subscriptions[subscription.stream_id].sort(
                key=lambda s: s.priority, reverse=True
            )

            async with self._metrics_lock:
                self._metrics["subscriptions_active"] += 1
                self._metrics["subscriptions_total"] += 1

            if self._enable_logging:
                logger.info(
                    f"Stream subscription created: {subscription.subscription_id} "
                    f"for stream {subscription.stream_id}"
                )

            # If stream is active, notify of start
            async with self._streams_lock:
                if subscription.stream_id in self._streams:
                    context = self._streams[subscription.stream_id]
                    if context.is_active and subscription.on_start is not None:
                        try:
                            subscription.on_start(subscription.stream_id)
                        except Exception as e:
                            logger.error(
                                f"Error in stream start handler: {e}"
                            )

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a stream.

        Args:
            subscription_id: ID of the subscription to remove.

        Returns:
            True if subscription was removed, False otherwise.

        Example:
            >>> protocol = StreamProtocol()
            >>> sub_id = protocol.subscribe(stream_id, handler)
            >>> protocol.unsubscribe(sub_id)
            True
        """
        return asyncio.run(self._unsubscribe_async(subscription_id))

    async def _unsubscribe_async(self, subscription_id: str) -> bool:
        """Async version of unsubscribe."""
        async with self._subscriptions_lock:
            for stream_id, subscriptions in self._subscriptions.items():
                for i, sub in enumerate(subscriptions):
                    if sub.subscription_id == subscription_id:
                        subscriptions.pop(i)

                        async with self._metrics_lock:
                            self._metrics["subscriptions_active"] -= 1

                        if self._enable_logging:
                            logger.info(
                                f"Stream subscription removed: {subscription_id} "
                                f"from stream {stream_id}"
                            )
                        return True
            return False

    def unsubscribe_all(self, stream_id: Optional[str] = None) -> int:
        """
        Unsubscribe all handlers from a stream or all streams.

        Args:
            stream_id: Specific stream to clear (optional).

        Returns:
            Number of subscriptions removed.

        Example:
            >>> protocol = StreamProtocol()
            >>> protocol.subscribe(stream_id, handler1)
            >>> protocol.subscribe(stream_id, handler2)
            >>> count = protocol.unsubscribe_all(stream_id)
            >>> count
            2
        """
        return asyncio.run(self._unsubscribe_all_async(stream_id))

    async def _unsubscribe_all_async(self, stream_id: Optional[str] = None) -> int:
        """Async version of unsubscribe_all."""
        count = 0

        if stream_id is not None:
            async with self._subscriptions_lock:
                if stream_id in self._subscriptions:
                    count = len(self._subscriptions[stream_id])
                    self._subscriptions[stream_id].clear()

                    async with self._metrics_lock:
                        self._metrics["subscriptions_active"] -= count
        else:
            async with self._subscriptions_lock:
                for sid in list(self._subscriptions.keys()):
                    count += len(self._subscriptions[sid])
                    self._subscriptions[sid].clear()

                async with self._metrics_lock:
                    self._metrics["subscriptions_active"] = 0

        return count

    async def _notify_stream_end(
        self, stream_id: str, error: Optional[Exception] = None
    ) -> None:
        """
        Notify subscribers of stream end.

        Args:
            stream_id: ID of the stream that ended.
            error: Optional error that caused the stream to end.
        """
        async with self._subscriptions_lock:
            if stream_id not in self._subscriptions:
                return

            for sub in self._subscriptions[stream_id]:
                if sub.on_end is not None:
                    try:
                        sub.on_end(stream_id, error)
                    except Exception as e:
                        logger.error(
                            f"Error in stream end handler: {e}"
                        )

    def get_stream(self, stream_id: str) -> Optional[StreamContext]:
        """
        Get information about a stream.

        Args:
            stream_id: ID of the stream.

        Returns:
            StreamContext if found, None otherwise.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> stream = protocol.get_stream(stream_id)
        """
        return self._streams.get(stream_id)

    def list_streams(self) -> List[str]:
        """
        List all active stream IDs.

        Returns:
            List of stream IDs.

        Example:
            >>> protocol = StreamProtocol()
            >>> stream_id = asyncio.run(protocol.create_stream("source", "destination"))
            >>> protocol.list_streams()
            ['...']
        """
        return list(self._streams.keys())

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get stream protocol metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> protocol = StreamProtocol()
            >>> metrics = protocol.get_metrics()
            >>> metrics["streams_created"]
            0
        """
        return {
            **self._metrics,
            "streams_count": len(self._streams),
            "subscriptions_count": self._metrics["subscriptions_active"],
        }

    def shutdown(self) -> None:
        """
        Shutdown stream protocol.

        Cleans up resources and stops all processing.

        Example:
            >>> protocol = StreamProtocol()
            >>> protocol.shutdown()
        """
        self._streams.clear()
        self._subscriptions.clear()
        self._metrics.clear()

        logger.info("Stream protocol shutdown complete")

    async def _find_matching_subscriptions(
        self, chunk: "StreamMessage"
    ) -> List[StreamSubscription]:
        """
        Find all subscriptions that match the given stream chunk.

        Args:
            chunk: The stream chunk to match.

        Returns:
            List of matching subscriptions.
        """
        async with self._subscriptions_lock:
            if chunk.stream_id not in self._subscriptions:
                return []

            return list(self._subscriptions[chunk.stream_id])

    def _validate_chunk(self, chunk: "StreamMessage") -> None:
        """
        Validate a stream chunk before sending.

        Args:
            chunk: Chunk to validate.

        Raises:
            MessageValidationError: If chunk is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not chunk.sender_id:
            raise MessageValidationError(
                "Stream chunk sender_id is required",
                message_id=chunk.message_id,
                validation_errors=["sender_id is required"],
            )

        if chunk.chunk_size > self._max_chunk_size:
            raise MessageValidationError(
                f"Stream chunk size {chunk.chunk_size} exceeds maximum {self._max_chunk_size}",
                message_id=chunk.message_id,
                validation_errors=[f"chunk_size too large: {chunk.chunk_size}"],
            )

    def __repr__(self) -> str:
        """Return string representation of the stream protocol."""
        return (
            f"StreamProtocol("
            f"streams={len(self._streams)}, "
            f"subscriptions={self._metrics['subscriptions_active']})"
        )
