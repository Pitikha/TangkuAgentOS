"""
Runtime Communication Framework - Broadcast Bus Implementation

The BroadcastBus provides a specialized message bus for one-to-many communication
patterns. It supports:
- Broadcast to all subscribers
- Notification with acknowledgment
- Channel-based broadcasting
- Message filtering
- Delivery tracking

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
        Broadcast,
        Notification,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IBroadcastBus,
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class BroadcastSubscription:
    """
    Represents a subscription to broadcast messages.

    Attributes:
        subscription_id: Unique identifier for the subscription.
        channels: List of channels to subscribe to (None for all).
        handler: Handler function to call for matching broadcasts.
        filter_func: Optional filter function for message matching.
        priority: Subscription priority (higher = processed first).
        active: Whether the subscription is active.
        message_count: Number of messages processed.
        error_count: Number of errors during processing.
        requires_ack: Whether acknowledgment is required.
        ack_timeout: Timeout for acknowledgment in seconds.
    """

    subscription_id: str
    channels: Optional[List[str]] = None
    handler: "IMessageHandler[Message]" = field(default_factory=lambda: None)
    filter_func: Optional[Callable[["Broadcast"], bool]] = None
    priority: int = 0
    active: bool = True
    message_count: int = 0
    error_count: int = 0
    requires_ack: bool = False
    ack_timeout: float = 60.0

    def matches(self, broadcast: "Broadcast") -> bool:
        """
        Check if this subscription matches the given broadcast.

        Args:
            broadcast: The broadcast to check.

        Returns:
            True if the subscription matches, False otherwise.
        """
        if not self.active:
            return False

        # Check channels
        if self.channels is not None:
            broadcast_channels = broadcast.channels or []
            if not any(c in broadcast_channels for c in self.channels):
                return False

        # Check filter function
        if self.filter_func is not None:
            try:
                return self.filter_func(broadcast)
            except Exception as e:
                logger.error(f"Error in broadcast subscription filter: {e}")
                return False

        return True

    async def process(self, broadcast: "Broadcast") -> Any:
        """
        Process a broadcast with this subscription.

        Args:
            broadcast: The broadcast to process.

        Returns:
            Result from the handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not self.active:
            return None

        self.message_count += 1
        try:
            return await self.handler.handle(broadcast)
        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Error processing broadcast in subscription {self.subscription_id}: {e}"
            )
            raise


class BroadcastBus:
    """
    Specialized message bus for one-to-many communication patterns.

    The BroadcastBus implements broadcast and notification patterns where
    messages are sent to multiple recipients. It supports:
    - Broadcast to all subscribers
    - Notification with acknowledgment
    - Channel-based broadcasting
    - Message filtering
    - Delivery tracking

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.buses.broadcast_bus import BroadcastBus
        >>> from tangku_agentos.runtime_communication.models.messages import Broadcast, MessageType
        >>> 
        >>> bus = BroadcastBus()
        >>> 
        >>> # Subscribe to broadcasts
        >>> class MyBroadcastHandler:
        ...     async def handle(self, message):
        ...         print(f"Broadcast received: {message.broadcast_type}")
        >>> 
        >>> handler = MyBroadcastHandler()
        >>> bus.subscribe(handler, channels=["system"])
        >>> 
        >>> # Broadcast a message
        >>> broadcast = Broadcast(
        ...     message_type=MessageType.BROADCAST,
        ...     sender_id="kernel",
        ...     broadcast_type="system.notification",
        ...     payload={"message": "System update"},
        ...     channels=["system"]
        ... )
        >>> asyncio.run(bus.broadcast(broadcast))

    Attributes:
        max_broadcast_history: Maximum number of broadcasts to keep in history.
    """

    def __init__(
        self,
        max_broadcast_history: int = 10000,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the broadcast bus.

        Args:
            max_broadcast_history: Maximum broadcasts to keep in history.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Subscriptions: List[BroadcastSubscription]
        self._subscriptions: List[BroadcastSubscription] = []
        self._subscriptions_lock = asyncio.Lock()

        # Broadcast history
        self._broadcast_history: List["Broadcast"] = []
        self._broadcast_history_lock = asyncio.Lock()
        self._max_broadcast_history = max_broadcast_history

        # Notification tracking
        self._pending_acks: Dict[str, Set[str]] = {}  # notification_id -> set of runtime_ids
        self._acks_lock = asyncio.Lock()

        # Metrics
        self._metrics: Dict[str, Any] = {
            "broadcasts_sent": 0,
            "broadcasts_delivered": 0,
            "broadcasts_failed": 0,
            "notifications_sent": 0,
            "notifications_acked": 0,
            "subscriptions_active": 0,
            "subscriptions_total": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"BroadcastBus initialized with max_history={max_broadcast_history}"
        )

    async def broadcast(
        self,
        broadcast: "Broadcast",
        channels: Optional[List[str]] = None,
    ) -> int:
        """
        Broadcast a message to all subscribers.

        Args:
            broadcast: Broadcast message to send.
            channels: Specific channels to broadcast to (overrides broadcast.channels).

        Returns:
            Number of subscribers notified.

        Raises:
            MessageValidationError: If broadcast validation fails.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Broadcast, MessageType
            >>> 
            >>> bus = BroadcastBus()
            >>> broadcast = Broadcast(
            ...     message_type=MessageType.BROADCAST,
            ...     sender_id="kernel",
            ...     broadcast_type="system.notification",
            ...     payload={"message": "System update"}
            ... )
            >>> count = asyncio.run(bus.broadcast(broadcast))
        """
        # Validate broadcast
        self._validate_broadcast(broadcast)

        # Set channels if provided
        if channels is not None:
            broadcast.channels = channels

        # Set timestamp if not set
        if broadcast.created_at is None:
            broadcast.created_at = datetime.utcnow()

        # Update metrics
        async with self._metrics_lock:
            self._metrics["broadcasts_sent"] += 1

        # Record broadcast in history
        await self._record_broadcast(broadcast)

        # Find matching subscriptions
        matching_subscriptions = await self._find_matching_subscriptions(broadcast)

        if not matching_subscriptions:
            if self._enable_logging:
                logger.debug(
                    f"No subscribers for broadcast: {broadcast.broadcast_type}"
                )
            return 0

        # Process broadcast with all matching subscriptions
        tasks = []
        for sub in matching_subscriptions:
            task = asyncio.create_task(sub.process(broadcast))
            tasks.append(task)

        # Wait for all tasks to complete (fire-and-forget)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update delivered count
        delivered_count = sum(
            1 for r in results if not isinstance(r, Exception)
        )
        async with self._metrics_lock:
            self._metrics["broadcasts_delivered"] += delivered_count

        # Log errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"Error processing broadcast {broadcast.message_id}: {result}"
                )
                async with self._metrics_lock:
                    self._metrics["broadcasts_failed"] += 1

        return len(matching_subscriptions)

    async def notify(
        self,
        notification: "Notification",
        requires_ack: Optional[bool] = None,
        ack_timeout: Optional[float] = None,
    ) -> int:
        """
        Send a notification to all subscribers.

        Notifications are similar to broadcasts but can request acknowledgment
        from recipients.

        Args:
            notification: Notification to send.
            requires_ack: Whether acknowledgment is required (overrides notification.requires_ack).
            ack_timeout: Timeout for acknowledgment in seconds (overrides notification.ack_timeout).

        Returns:
            Number of subscribers notified.

        Raises:
            MessageValidationError: If notification validation fails.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Notification, MessageType
            >>> 
            >>> bus = BroadcastBus()
            >>> notification = Notification(
            ...     message_type=MessageType.NOTIFICATION,
            ...     sender_id="kernel",
            ...     notification_type="system.alert",
            ...     payload={"message": "Critical alert"},
            ...     requires_ack=True
            ... )
            >>> count = asyncio.run(bus.notify(notification))
        """
        # Validate notification
        self._validate_notification(notification)

        # Override notification settings if provided
        if requires_ack is not None:
            notification.requires_ack = requires_ack
        if ack_timeout is not None:
            notification.ack_timeout = ack_timeout

        # Set timestamp if not set
        if notification.created_at is None:
            notification.created_at = datetime.utcnow()

        # Update metrics
        async with self._metrics_lock:
            self._metrics["notifications_sent"] += 1

        # Track acknowledgments if required
        if notification.requires_ack:
            async with self._acks_lock:
                self._pending_acks[notification.message_id] = set()

        # Convert notification to broadcast for processing
        broadcast = Broadcast(
            message_id=notification.message_id,
            message_type=MessageType.NOTIFICATION,
            sender_id=notification.sender_id,
            recipient_id=notification.recipient_id,
            payload=notification.payload,
            priority=notification.priority,
            created_at=notification.created_at,
            expires_at=notification.expires_at,
            correlation_id=notification.correlation_id,
            reply_to=notification.reply_to,
            conversation_id=notification.conversation_id,
            status=notification.status,
            delivery_attempts=notification.delivery_attempts,
            max_retries=notification.max_retries,
            metadata=notification.metadata,
            tags=notification.tags,
            headers=notification.headers,
            broadcast_type=notification.notification_type,
            channels=None,  # Use subscriptions' channels
        )

        # Send as broadcast
        count = await self.broadcast(broadcast)

        return count

    def subscribe(
        self,
        handler: "IMessageHandler[Message]",
        channels: Optional[List[str]] = None,
        filter_func: Optional[Callable[["Broadcast"], bool]] = None,
        priority: int = 0,
        requires_ack: bool = False,
        ack_timeout: float = 60.0,
    ) -> str:
        """
        Subscribe to broadcast messages.

        Args:
            handler: Handler to call for matching broadcasts.
            channels: List of channels to subscribe to (None for all).
            filter_func: Optional filter function for message matching.
            priority: Subscription priority (higher = processed first).
            requires_ack: Whether acknowledgment is required.
            ack_timeout: Timeout for acknowledgment in seconds.

        Returns:
            Subscription ID.

        Example:
            >>> class MyBroadcastHandler:
            ...     async def handle(self, message):
            ...         print(f"Broadcast: {message.broadcast_type}")
            >>> 
            >>> bus = BroadcastBus()
            >>> handler = MyBroadcastHandler()
            >>> sub_id = bus.subscribe(handler, channels=["system"])
        """
        subscription_id = str(uuid.uuid4())

        subscription = BroadcastSubscription(
            subscription_id=subscription_id,
            channels=channels,
            handler=handler,
            filter_func=filter_func,
            priority=priority,
            requires_ack=requires_ack,
            ack_timeout=ack_timeout,
        )

        asyncio.run(self._subscribe_async(subscription))
        return subscription_id

    async def _subscribe_async(self, subscription: BroadcastSubscription) -> None:
        """Async version of subscribe."""
        async with self._subscriptions_lock:
            self._subscriptions.append(subscription)
            self._subscriptions.sort(key=lambda s: s.priority, reverse=True)

            async with self._metrics_lock:
                self._metrics["subscriptions_active"] += 1
                self._metrics["subscriptions_total"] += 1

            if self._enable_logging:
                logger.info(
                    f"Broadcast handler subscribed: {subscription.subscription_id}"
                )

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from broadcasts.

        Args:
            subscription_id: ID of the subscription to remove.

        Returns:
            True if subscription was removed, False otherwise.

        Example:
            >>> bus = BroadcastBus()
            >>> sub_id = bus.subscribe(handler)
            >>> bus.unsubscribe(sub_id)
            True
        """
        return asyncio.run(self._unsubscribe_async(subscription_id))

    async def _unsubscribe_async(self, subscription_id: str) -> bool:
        """Async version of unsubscribe."""
        async with self._subscriptions_lock:
            for i, sub in enumerate(self._subscriptions):
                if sub.subscription_id == subscription_id:
                    self._subscriptions.pop(i)

                    async with self._metrics_lock:
                        self._metrics["subscriptions_active"] -= 1

                    if self._enable_logging:
                        logger.info(f"Broadcast subscription {subscription_id} removed")
                    return True
            return False

    def unsubscribe_all(self) -> int:
        """
        Unsubscribe all handlers.

        Returns:
            Number of subscriptions removed.

        Example:
            >>> bus = BroadcastBus()
            >>> bus.subscribe(handler1)
            >>> bus.subscribe(handler2)
            >>> count = bus.unsubscribe_all()
            >>> count
            2
        """
        return asyncio.run(self._unsubscribe_all_async())

    async def _unsubscribe_all_async(self) -> int:
        """Async version of unsubscribe_all."""
        async with self._subscriptions_lock:
            count = len(self._subscriptions)
            self._subscriptions.clear()

            async with self._metrics_lock:
                self._metrics["subscriptions_active"] = 0

        return count

    async def acknowledge(
        self, notification_id: str, runtime_id: str
    ) -> bool:
        """
        Acknowledge a notification.

        Args:
            notification_id: ID of the notification to acknowledge.
            runtime_id: ID of the runtime acknowledging.

        Returns:
            True if acknowledgment was recorded, False otherwise.

        Example:
            >>> bus = BroadcastBus()
            >>> # Assume notification was sent
            >>> bus.acknowledge("notif-123", "runtime-1")
            True
        """
        async with self._acks_lock:
            if notification_id in self._pending_acks:
                self._pending_acks[notification_id].add(runtime_id)

                async with self._metrics_lock:
                    self._metrics["notifications_acked"] += 1

                return True
            return False

    def is_acknowledged(
        self, notification_id: str, expected_runtimes: Optional[List[str]] = None
    ) -> bool:
        """
        Check if a notification has been acknowledged by all expected runtimes.

        Args:
            notification_id: ID of the notification to check.
            expected_runtimes: List of runtime IDs that should acknowledge.

        Returns:
            True if all expected runtimes have acknowledged, False otherwise.

        Example:
            >>> bus = BroadcastBus()
            >>> bus.acknowledge("notif-123", "runtime-1")
            True
            >>> bus.is_acknowledged("notif-123", ["runtime-1"])
            True
        """
        async with self._acks_lock:
            if notification_id not in self._pending_acks:
                return False

            acked_runtimes = self._pending_acks[notification_id]

            if expected_runtimes is None:
                return True

            return set(expected_runtimes).issubset(acked_runtimes)

    def get_broadcast_history(
        self,
        broadcast_type: Optional[str] = None,
        limit: int = 100,
    ) -> List["Broadcast"]:
        """
        Retrieve broadcast history with optional filtering.

        Args:
            broadcast_type: Filter by broadcast type (optional).
            limit: Maximum broadcasts to return.

        Returns:
            List of broadcasts.

        Example:
            >>> bus = BroadcastBus()
            >>> # Broadcast some messages
            >>> history = bus.get_broadcast_history(limit=10)
        """
        broadcasts = list(self._broadcast_history)

        if broadcast_type is not None:
            broadcasts = [
                b for b in broadcasts if b.broadcast_type == broadcast_type
            ]

        return broadcasts[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get broadcast bus metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> bus = BroadcastBus()
            >>> metrics = bus.get_metrics()
            >>> metrics["broadcasts_sent"]
            0
        """
        return {
            **self._metrics,
            "broadcast_history_size": len(self._broadcast_history),
            "active_subscriptions": self._metrics["subscriptions_active"],
            "total_subscriptions": self._metrics["subscriptions_total"],
            "pending_acks": len(self._pending_acks),
        }

    def clear_history(self) -> int:
        """
        Clear broadcast history.

        Returns:
            Count of broadcasts cleared.

        Example:
            >>> bus = BroadcastBus()
            >>> count = bus.clear_history()
        """
        count = len(self._broadcast_history)
        self._broadcast_history.clear()
        return count

    def clear_acks(self) -> int:
        """
        Clear pending acknowledgments.

        Returns:
            Count of acknowledgment sets cleared.

        Example:
            >>> bus = BroadcastBus()
            >>> count = bus.clear_acks()
        """
        count = len(self._pending_acks)
        self._pending_acks.clear()
        return count

    def shutdown(self) -> None:
        """
        Shutdown broadcast bus.

        Cleans up resources and stops all processing.

        Example:
            >>> bus = BroadcastBus()
            >>> bus.shutdown()
        """
        self._broadcast_history.clear()
        self._subscriptions.clear()
        self._pending_acks.clear()
        self._metrics.clear()

        logger.info("Broadcast bus shutdown complete")

    async def _find_matching_subscriptions(
        self, broadcast: "Broadcast"
    ) -> List[BroadcastSubscription]:
        """
        Find all subscriptions that match the given broadcast.

        Args:
            broadcast: The broadcast to match.

        Returns:
            List of matching subscriptions.
        """
        async with self._subscriptions_lock:
            subscriptions = list(self._subscriptions)

        # Filter by match
        return [
            sub for sub in subscriptions if sub.matches(broadcast)
        ]

    async def _record_broadcast(self, broadcast: "Broadcast") -> None:
        """
        Store broadcast in history.

        Args:
            broadcast: Broadcast to store.
        """
        async with self._broadcast_history_lock:
            self._broadcast_history.append(broadcast)
            if len(self._broadcast_history) > self._max_broadcast_history:
                self._broadcast_history.pop(0)

    def _validate_broadcast(self, broadcast: "Broadcast") -> None:
        """
        Validate a broadcast before sending.

        Args:
            broadcast: Broadcast to validate.

        Raises:
            MessageValidationError: If broadcast is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not broadcast.sender_id:
            raise MessageValidationError(
                "Broadcast sender_id is required",
                message_id=broadcast.message_id,
                validation_errors=["sender_id is required"],
            )

        if not broadcast.broadcast_type:
            raise MessageValidationError(
                "Broadcast broadcast_type is required",
                message_id=broadcast.message_id,
                validation_errors=["broadcast_type is required"],
            )

    def _validate_notification(self, notification: "Notification") -> None:
        """
        Validate a notification before sending.

        Args:
            notification: Notification to validate.

        Raises:
            MessageValidationError: If notification is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not notification.sender_id:
            raise MessageValidationError(
                "Notification sender_id is required",
                message_id=notification.message_id,
                validation_errors=["sender_id is required"],
            )

        if not notification.notification_type:
            raise MessageValidationError(
                "Notification notification_type is required",
                message_id=notification.message_id,
                validation_errors=["notification_type is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the broadcast bus."""
        return (
            f"BroadcastBus("
            f"subscriptions={self._metrics['subscriptions_active']}, "
            f"history={len(self._broadcast_history)}, "
            f"pending_acks={len(self._pending_acks)})"
        )
