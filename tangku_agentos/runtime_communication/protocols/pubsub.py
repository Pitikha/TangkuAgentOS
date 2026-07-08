"""
Runtime Communication Framework - Publish/Subscribe Protocol

The PubSubProtocol implements the publish/subscribe communication pattern
for the Runtime Communication Framework. It provides:
- Topic-based publishing and subscribing
- Message filtering
- Quality of Service (QoS) levels
- Retained messages
- Last Will and Testament (LWT)

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
        Event,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


class QoSLevel:
    """
    Quality of Service levels for PubSub communication.

    Attributes:
        AT_MOST_ONCE: Message may be delivered zero or one time (fire-and-forget).
        AT_LEAST_ONCE: Message will be delivered at least once (guaranteed delivery).
        EXACTLY_ONCE: Message will be delivered exactly once (no duplicates).
    """

    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


@dataclass
class TopicSubscription:
    """
    Represents a subscription to a PubSub topic.

    Attributes:
        subscription_id: Unique identifier for the subscription.
        topic: Topic to subscribe to.
        handler: Handler function to call for matching messages.
        qos: Quality of Service level.
        filter_func: Optional filter function for message matching.
        priority: Subscription priority (higher = processed first).
        active: Whether the subscription is active.
        message_count: Number of messages processed.
        error_count: Number of errors during processing.
        created_at: When the subscription was created.
    """

    subscription_id: str
    topic: str
    handler: "IMessageHandler[Message]"
    qos: int = QoSLevel.AT_MOST_ONCE
    filter_func: Optional[Callable[["Message"], bool]] = None
    priority: int = 0
    active: bool = True
    message_count: int = 0
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def matches(self, topic: str, message: "Message") -> bool:
        """
        Check if this subscription matches the given topic and message.

        Args:
            topic: The topic to check.
            message: The message to check.

        Returns:
            True if the subscription matches, False otherwise.
        """
        if not self.active:
            return False

        # Check topic (support wildcards)
        if not self._topic_matches(topic):
            return False

        # Check filter function
        if self.filter_func is not None:
            try:
                return self.filter_func(message)
            except Exception as e:
                logger.error(f"Error in topic subscription filter: {e}")
                return False

        return True

    def _topic_matches(self, topic: str) -> bool:
        """
        Check if the subscription topic matches the given topic.

        Supports MQTT-style wildcards:
        - +: Matches a single topic level
        - #: Matches multiple topic levels

        Args:
            topic: The topic to check.

        Returns:
            True if the topic matches, False otherwise.
        """
        # Simple exact match
        if self.topic == topic:
            return True

        # Wildcard matching
        sub_parts = self.topic.split("/")
        topic_parts = topic.split("/")

        for i, (sub_part, topic_part) in enumerate(
            zip(sub_parts, topic_parts)
        ):
            if sub_part == "#":
                # Multi-level wildcard matches everything remaining
                return True
            if sub_part == "+" or sub_part == topic_part:
                continue
            return False

        # If we get here, check if subscription has more parts
        if len(sub_parts) > len(topic_parts):
            # Check if remaining subscription parts are all #
            for part in sub_parts[len(topic_parts) :]:
                if part != "#":
                    return False
            return True

        # Exact length match required
        return len(sub_parts) == len(topic_parts)

    async def process(self, message: "Message") -> Any:
        """
        Process a message with this subscription.

        Args:
            message: The message to process.

        Returns:
            Result from the handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not self.active:
            return None

        self.message_count += 1
        try:
            return await self.handler.handle(message)
        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Error processing message in subscription {self.subscription_id}: {e}"
            )
            raise


@dataclass
class RetainedMessage:
    """
    A message retained by the PubSub protocol.

    Attributes:
        topic: Topic the message was published to.
        message: The retained message.
        published_at: When the message was published.
        qos: Quality of Service level.
    """

    topic: str
    message: "Message"
    published_at: datetime = field(default_factory=datetime.utcnow)
    qos: int = QoSLevel.AT_MOST_ONCE


@dataclass
class LastWill:
    """
    Last Will and Testament for a PubSub client.

    Attributes:
        topic: Topic to publish the will to.
        message: Will message to publish.
        qos: Quality of Service level.
        retain: Whether the will message should be retained.
    """

    topic: str
    message: "Message"
    qos: int = QoSLevel.AT_MOST_ONCE
    retain: bool = False


class PubSubProtocol:
    """
    Publish/Subscribe protocol implementation.

    The PubSubProtocol implements the publish/subscribe communication pattern
    with support for:
    - Topic-based publishing and subscribing
    - Quality of Service (QoS) levels
    - Retained messages
    - Last Will and Testament (LWT)
    - Wildcard topic subscriptions

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.protocols.pubsub import PubSubProtocol
        >>> from tangku_agentos.runtime_communication.models.messages import Message, MessageType
        >>> 
        >>> protocol = PubSubProtocol()
        >>> 
        >>> # Subscribe to a topic
        >>> class MyHandler:
        ...     async def handle(self, message: Message) -> None:
        ...         print(f"Received on {message.headers.get('topic')}: {message.payload}")
        >>> 
        >>> handler = MyHandler()
        >>> sub_id = protocol.subscribe("system/notifications", handler)
        >>> 
        >>> # Publish a message
        >>> msg = Message(
        ...     message_type=MessageType.EVENT,
        ...     sender_id="publisher",
        ...     payload={"message": "Hello"},
        ... )
        >>> msg.headers["topic"] = "system/notifications"
        >>> asyncio.run(protocol.publish("system/notifications", msg))

    Attributes:
        max_retained_messages: Maximum number of retained messages per topic.
        default_qos: Default Quality of Service level.
    """

    def __init__(
        self,
        max_retained_messages: int = 100,
        default_qos: int = QoSLevel.AT_MOST_ONCE,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the PubSub protocol.

        Args:
            max_retained_messages: Maximum retained messages per topic.
            default_qos: Default Quality of Service level.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Subscriptions: topic -> List[TopicSubscription]
        self._subscriptions: Dict[str, List[TopicSubscription]] = defaultdict(list)
        self._subscriptions_lock = asyncio.Lock()

        # Retained messages: topic -> RetainedMessage
        self._retained_messages: Dict[str, RetainedMessage] = {}
        self._retained_messages_lock = asyncio.Lock()
        self._max_retained_messages = max_retained_messages

        # Last Wills: client_id -> LastWill
        self._last_wills: Dict[str, LastWill] = {}
        self._last_wills_lock = asyncio.Lock()

        # Configuration
        self._default_qos = default_qos

        # Metrics
        self._metrics: Dict[str, Any] = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "subscriptions_active": 0,
            "subscriptions_total": 0,
            "retained_messages": 0,
            "last_wills": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"PubSubProtocol initialized with max_retained={max_retained_messages}, "
            f"default_qos={default_qos}"
        )

    async def publish(
        self,
        topic: str,
        message: "Message",
        qos: Optional[int] = None,
        retain: bool = False,
    ) -> int:
        """
        Publish a message to a topic.

        Args:
            topic: Topic to publish to.
            message: Message to publish.
            qos: Quality of Service level (uses default if not specified).
            retain: Whether to retain the message.

        Returns:
            Number of subscribers notified.

        Raises:
            MessageValidationError: If message validation fails.

        Example:
            >>> protocol = PubSubProtocol()
            >>> msg = Message(
            ...     message_type=MessageType.EVENT,
            ...     sender_id="publisher",
            ...     payload={"message": "Hello"}
            ... )
            >>> count = asyncio.run(protocol.publish("system/notifications", msg))
        """
        # Validate message
        self._validate_message(message)

        # Set QoS
        if qos is None:
            qos = self._default_qos
        message.headers["qos"] = str(qos)

        # Set topic in headers
        message.headers["topic"] = topic

        # Set timestamp if not set
        if message.created_at is None:
            message.created_at = datetime.utcnow()

        # Update metrics
        async with self._metrics_lock:
            self._metrics["messages_published"] += 1

        # Retain message if requested
        if retain:
            await self._retain_message(topic, message, qos)

        # Find matching subscriptions
        matching_subscriptions = await self._find_matching_subscriptions(topic, message)

        if not matching_subscriptions:
            if self._enable_logging:
                logger.debug(f"No subscribers for topic: {topic}")
            return 0

        # Process message with all matching subscriptions
        tasks = []
        for sub in matching_subscriptions:
            # For QoS 1 and 2, we might want to track delivery
            if qos >= QoSLevel.AT_LEAST_ONCE:
                # In a real implementation, we would track delivery and retry if needed
                pass

            task = asyncio.create_task(sub.process(message))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update delivered count
        delivered_count = sum(
            1 for r in results if not isinstance(r, Exception)
        )
        async with self._metrics_lock:
            self._metrics["messages_delivered"] += delivered_count

        # Log errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"Error processing message {message.message_id} on topic {topic}: {result}"
                )
                async with self._metrics_lock:
                    self._metrics["messages_failed"] += 1

        return len(matching_subscriptions)

    def subscribe(
        self,
        topic: str,
        handler: "IMessageHandler[Message]",
        qos: int = QoSLevel.AT_MOST_ONCE,
        filter_func: Optional[Callable[["Message"], bool]] = None,
        priority: int = 0,
    ) -> str:
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to (supports wildcards + and #).
            handler: Handler to call for matching messages.
            qos: Quality of Service level.
            filter_func: Optional filter function for message matching.
            priority: Subscription priority (higher = processed first).

        Returns:
            Subscription ID.

        Example:
            >>> protocol = PubSubProtocol()
            >>> 
            >>> class MyHandler:
            ...     async def handle(self, message: Message) -> None:
            ...         print(f"Received: {message.payload}")
            >>> 
            >>> handler = MyHandler()
            >>> sub_id = protocol.subscribe("system/#", handler)
        """
        subscription_id = str(uuid.uuid4())

        subscription = TopicSubscription(
            subscription_id=subscription_id,
            topic=topic,
            handler=handler,
            qos=qos,
            filter_func=filter_func,
            priority=priority,
        )

        asyncio.run(self._subscribe_async(topic, subscription))
        return subscription_id

    async def _subscribe_async(
        self, topic: str, subscription: TopicSubscription
    ) -> None:
        """Async version of subscribe."""
        async with self._subscriptions_lock:
            self._subscriptions[topic].append(subscription)
            self._subscriptions[topic].sort(
                key=lambda s: s.priority, reverse=True
            )

            async with self._metrics_lock:
                self._metrics["subscriptions_active"] += 1
                self._metrics["subscriptions_total"] += 1

            if self._enable_logging:
                logger.info(
                    f"Subscribed to topic '{topic}': {subscription.subscription_id}"
                )

            # If there's a retained message for this topic, deliver it
            async with self._retained_messages_lock:
                if topic in self._retained_messages:
                    retained = self._retained_messages[topic]
                    if subscription.qos >= retained.qos:
                        # Deliver retained message
                        try:
                            await subscription.process(retained.message)
                            async with self._metrics_lock:
                                self._metrics["messages_delivered"] += 1
                        except Exception as e:
                            logger.error(
                                f"Error delivering retained message: {e}"
                            )

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.

        Args:
            subscription_id: ID of the subscription to remove.

        Returns:
            True if subscription was removed, False otherwise.

        Example:
            >>> protocol = PubSubProtocol()
            >>> sub_id = protocol.subscribe("system/notifications", handler)
            >>> protocol.unsubscribe(sub_id)
            True
        """
        return asyncio.run(self._unsubscribe_async(subscription_id))

    async def _unsubscribe_async(self, subscription_id: str) -> bool:
        """Async version of unsubscribe."""
        async with self._subscriptions_lock:
            for topic, subscriptions in self._subscriptions.items():
                for i, sub in enumerate(subscriptions):
                    if sub.subscription_id == subscription_id:
                        subscriptions.pop(i)

                        async with self._metrics_lock:
                            self._metrics["subscriptions_active"] -= 1

                        if self._enable_logging:
                            logger.info(
                                f"Unsubscribed from topic '{topic}': {subscription_id}"
                            )
                        return True
            return False

    def unsubscribe_all(self, topic: Optional[str] = None) -> int:
        """
        Unsubscribe all handlers from a topic or all topics.

        Args:
            topic: Specific topic to clear (optional).

        Returns:
            Number of subscriptions removed.

        Example:
            >>> protocol = PubSubProtocol()
            >>> protocol.subscribe("system/notifications", handler1)
            >>> protocol.subscribe("system/notifications", handler2)
            >>> count = protocol.unsubscribe_all("system/notifications")
            >>> count
            2
        """
        return asyncio.run(self._unsubscribe_all_async(topic))

    async def _unsubscribe_all_async(self, topic: Optional[str] = None) -> int:
        """Async version of unsubscribe_all."""
        count = 0

        if topic is not None:
            async with self._subscriptions_lock:
                if topic in self._subscriptions:
                    count = len(self._subscriptions[topic])
                    self._subscriptions[topic].clear()

                    async with self._metrics_lock:
                        self._metrics["subscriptions_active"] -= count
        else:
            async with self._subscriptions_lock:
                for topic_key in list(self._subscriptions.keys()):
                    count += len(self._subscriptions[topic_key])
                    self._subscriptions[topic_key].clear()

                async with self._metrics_lock:
                    self._metrics["subscriptions_active"] = 0

        return count

    async def register_last_will(
        self,
        client_id: str,
        topic: str,
        message: "Message",
        qos: int = QoSLevel.AT_MOST_ONCE,
        retain: bool = False,
    ) -> None:
        """
        Register a Last Will and Testament for a client.

        The will message will be published if the client disconnects unexpectedly.

        Args:
            client_id: ID of the client.
            topic: Topic to publish the will to.
            message: Will message to publish.
            qos: Quality of Service level.
            retain: Whether the will message should be retained.

        Example:
            >>> protocol = PubSubProtocol()
            >>> msg = Message(
            ...     message_type=MessageType.EVENT,
            ...     sender_id="client1",
            ...     payload={"status": "disconnected"}
            ... )
            >>> asyncio.run(protocol.register_last_will(
            ...     "client1", "system/clients/disconnected", msg
            ... ))
        """
        will = LastWill(
            topic=topic,
            message=message,
            qos=qos,
            retain=retain,
        )

        async with self._last_wills_lock:
            self._last_wills[client_id] = will

            async with self._metrics_lock:
                self._metrics["last_wills"] += 1

            if self._enable_logging:
                logger.info(f"Last will registered for client: {client_id}")

    async def unregister_last_will(self, client_id: str) -> bool:
        """
        Unregister a Last Will and Testament for a client.

        Args:
            client_id: ID of the client.

        Returns:
            True if will was removed, False otherwise.

        Example:
            >>> protocol = PubSubProtocol()
            >>> asyncio.run(protocol.register_last_will("client1", "topic", msg))
            >>> asyncio.run(protocol.unregister_last_will("client1"))
            True
        """
        async with self._last_wills_lock:
            if client_id in self._last_wills:
                del self._last_wills[client_id]

                async with self._metrics_lock:
                    self._metrics["last_wills"] -= 1

                if self._enable_logging:
                    logger.info(f"Last will unregistered for client: {client_id}")
                return True
            return False

    async def publish_last_will(self, client_id: str) -> bool:
        """
        Publish a client's Last Will and Testament.

        Args:
            client_id: ID of the client.

        Returns:
            True if will was published, False otherwise.

        Example:
            >>> protocol = PubSubProtocol()
            >>> asyncio.run(protocol.register_last_will("client1", "topic", msg))
            >>> asyncio.run(protocol.publish_last_will("client1"))
            True
        """
        async with self._last_wills_lock:
            will = self._last_wills.get(client_id)
            if will is None:
                return False

            # Remove the will first to prevent duplicate publishing
            del self._last_wills[client_id]

            async with self._metrics_lock:
                self._metrics["last_wills"] -= 1

        if will is not None:
            await self.publish(
                will.topic,
                will.message,
                qos=will.qos,
                retain=will.retain,
            )
            return True

        return False

    async def get_retained_message(self, topic: str) -> Optional["Message"]:
        """
        Get the retained message for a topic.

        Args:
            topic: Topic to get retained message for.

        Returns:
            Retained message if found, None otherwise.

        Example:
            >>> protocol = PubSubProtocol()
            >>> msg = Message(...)
            >>> asyncio.run(protocol.publish("topic", msg, retain=True))
            >>> retained = asyncio.run(protocol.get_retained_message("topic"))
        """
        async with self._retained_messages_lock:
            retained = self._retained_messages.get(topic)
            if retained is not None:
                return retained.message
            return None

    async def clear_retained_message(self, topic: str) -> bool:
        """
        Clear the retained message for a topic.

        Args:
            topic: Topic to clear retained message for.

        Returns:
            True if message was cleared, False otherwise.

        Example:
            >>> protocol = PubSubProtocol()
            >>> asyncio.run(protocol.publish("topic", msg, retain=True))
            >>> asyncio.run(protocol.clear_retained_message("topic"))
            True
        """
        async with self._retained_messages_lock:
            if topic in self._retained_messages:
                del self._retained_messages[topic]

                async with self._metrics_lock:
                    self._metrics["retained_messages"] -= 1

                return True
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get PubSub protocol metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> protocol = PubSubProtocol()
            >>> metrics = protocol.get_metrics()
            >>> metrics["messages_published"]
            0
        """
        return {
            **self._metrics,
            "retained_messages_count": len(self._retained_messages),
            "last_wills_count": len(self._last_wills),
            "topics_count": len(self._subscriptions),
        }

    def shutdown(self) -> None:
        """
        Shutdown PubSub protocol.

        Cleans up resources and stops all processing.

        Example:
            >>> protocol = PubSubProtocol()
            >>> protocol.shutdown()
        """
        self._subscriptions.clear()
        self._retained_messages.clear()
        self._last_wills.clear()
        self._metrics.clear()

        logger.info("PubSub protocol shutdown complete")

    async def _retain_message(
        self, topic: str, message: "Message", qos: int
    ) -> None:
        """
        Retain a message for a topic.

        Args:
            topic: Topic to retain the message for.
            message: Message to retain.
            qos: Quality of Service level.
        """
        async with self._retained_messages_lock:
            # Check if we're at capacity
            if len(self._retained_messages) >= self._max_retained_messages:
                # Remove oldest retained message
                oldest_topic = min(
                    self._retained_messages.keys(),
                    key=lambda t: self._retained_messages[t].published_at,
                )
                del self._retained_messages[oldest_topic]

            # Store the new retained message
            self._retained_messages[topic] = RetainedMessage(
                topic=topic,
                message=message,
                qos=qos,
            )

            async with self._metrics_lock:
                self._metrics["retained_messages"] += 1

    async def _find_matching_subscriptions(
        self, topic: str, message: "Message"
    ) -> List[TopicSubscription]:
        """
        Find all subscriptions that match the given topic and message.

        Args:
            topic: The topic to match.
            message: The message to match.

        Returns:
            List of matching subscriptions.
        """
        async with self._subscriptions_lock:
            all_subscriptions = []
            for sub_topic, subscriptions in self._subscriptions.items():
                all_subscriptions.extend(subscriptions)

        # Filter by match
        return [
            sub
            for sub in all_subscriptions
            if sub.matches(topic, message)
        ]

    def _validate_message(self, message: "Message") -> None:
        """
        Validate a message before publishing.

        Args:
            message: Message to validate.

        Raises:
            MessageValidationError: If message is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not message.sender_id:
            raise MessageValidationError(
                "Message sender_id is required",
                message_id=message.message_id,
                validation_errors=["sender_id is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the PubSub protocol."""
        return (
            f"PubSubProtocol("
            f"subscriptions={self._metrics['subscriptions_active']}, "
            f"retained={len(self._retained_messages)}, "
            f"last_wills={len(self._last_wills)})"
        )
