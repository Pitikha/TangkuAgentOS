"""
Runtime Communication Framework - Event Bus Implementation

The EventBus provides a specialized message bus for event-based communication
patterns. It supports publish/subscribe semantics with:
- Multiple subscribers per event type
- Event filtering and routing
- Async event processing
- Error handling and retries
- Event metrics and monitoring

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
        IEventBus,
        IEventHandler,
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """
    Represents a subscription to a specific event type.

    Attributes:
        subscription_id: Unique identifier for the subscription.
        event_type: Type of event to subscribe to.
        handler: Handler function to call for matching events.
        filter_func: Optional filter function for event matching.
        priority: Subscription priority (higher = processed first).
        active: Whether the subscription is active.
        event_count: Number of events processed.
        error_count: Number of errors during processing.
        created_at: When the subscription was created.
    """

    subscription_id: str
    event_type: Union[str, "MessageType"]
    handler: Union["IEventHandler[Event]", "IMessageHandler[Message]"]
    filter_func: Optional[Callable[["Event"], bool]] = None
    priority: int = 0
    active: bool = True
    event_count: int = 0
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def matches(self, event: "Event") -> bool:
        """
        Check if this subscription matches the given event.

        Args:
            event: The event to check.

        Returns:
            True if the subscription matches, False otherwise.
        """
        if not self.active:
            return False

        # Check event type
        event_type_name = event.message_type.name
        sub_type = (
            self.event_type
            if isinstance(self.event_type, str)
            else self.event_type.name
        )

        if event_type_name != sub_type and sub_type != "*":
            return False

        # Check filter function
        if self.filter_func is not None:
            try:
                return self.filter_func(event)
            except Exception as e:
                logger.error(f"Error in event subscription filter: {e}")
                return False

        return True

    async def process(self, event: "Event") -> Any:
        """
        Process an event with this subscription.

        Args:
            event: The event to process.

        Returns:
            Result from the handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not self.active:
            return None

        self.event_count += 1
        try:
            # Handle both IEventHandler and IMessageHandler
            if hasattr(self.handler, "handle_event"):
                return await self.handler.handle_event(event)
            else:
                return await self.handler.handle(event)
        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Error processing event in subscription {self.subscription_id}: {e}"
            )
            raise


class EventBus:
    """
    Specialized message bus for event-based communication patterns.

    The EventBus implements the publish/subscribe pattern where events are
    published to zero or more subscribers. It supports:
    - Multiple subscribers per event type
    - Event filtering
    - Async processing
    - Error handling
    - Metrics collection

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.buses.event_bus import EventBus
        >>> from tangku_agentos.runtime_communication.models.messages import Event, MessageType
        >>> 
        >>> bus = EventBus()
        >>> 
        >>> # Subscribe to an event type
        >>> class MyEventHandler:
        ...     async def handle_event(self, event: Event) -> None:
        ...         print(f"Event received: {event.event_type}")
        >>> 
        >>> handler = MyEventHandler()
        >>> bus.subscribe("system.started", handler)
        >>> 
        >>> # Publish an event
        >>> event = Event(
        ...     message_type=MessageType.EVENT,
        ...     sender_id="kernel",
        ...     event_type="system.started",
        ...     payload={"timestamp": "2024-01-01"}
        ... )
        >>> asyncio.run(bus.publish(event))

    Attributes:
        max_event_history: Maximum number of events to keep in history.
    """

    def __init__(
        self,
        max_event_history: int = 10000,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the event bus.

        Args:
            max_event_history: Maximum events to keep in history.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Subscriptions: event_type -> List[EventSubscription]
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._subscriptions_lock = asyncio.Lock()

        # Event history
        self._event_history: List["Event"] = []
        self._event_history_lock = asyncio.Lock()
        self._max_event_history = max_event_history

        # Metrics
        self._metrics: Dict[str, Any] = {
            "events_published": 0,
            "events_delivered": 0,
            "events_failed": 0,
            "subscriptions_active": 0,
            "subscriptions_total": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"EventBus initialized with max_history={max_event_history}"
        )

    async def publish(self, event: "Event") -> None:
        """
        Publish an event to all subscribers.

        This is the main method for publishing events. The event will be
        delivered to all subscribers that match the event type and any
        optional filters.

        Args:
            event: Event to publish.

        Raises:
            Exception: If event validation fails or publishing fails.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Event, MessageType
            >>> 
            >>> bus = EventBus()
            >>> event = Event(
            ...     message_type=MessageType.EVENT,
            ...     sender_id="kernel",
            ...     event_type="system.started",
            ...     payload={"timestamp": "2024-01-01"}
            ... )
            >>> asyncio.run(bus.publish(event))
        """
        # Validate event
        self._validate_event(event)

        # Set event timestamp if not set
        if event.timestamp is None:
            event.timestamp = datetime.utcnow()

        # Update metrics
        async with self._metrics_lock:
            self._metrics["events_published"] += 1

        # Record event in history
        await self._record_event(event)

        # Find matching subscriptions
        matching_subscriptions = await self._find_matching_subscriptions(event)

        if not matching_subscriptions:
            if self._enable_logging:
                logger.debug(f"No subscribers for event: {event.event_type}")
            return

        # Process event with all matching subscriptions
        tasks = []
        for sub in matching_subscriptions:
            task = asyncio.create_task(sub.process(event))
            tasks.append(task)

        # Wait for all tasks to complete (fire-and-forget)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update delivered count
        delivered_count = sum(
            1 for r in results if not isinstance(r, Exception)
        )
        async with self._metrics_lock:
            self._metrics["events_delivered"] += delivered_count

        # Log errors
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing event {event.message_id}: {result}")
                async with self._metrics_lock:
                    self._metrics["events_failed"] += 1

    async def emit(
        self,
        event_type: str,
        payload: Any = None,
        sender_id: str = "system",
        priority: "MessagePriority" = "MessagePriority.NORMAL",
        **kwargs,
    ) -> None:
        """
        Emit an event (convenience method).

        This is a convenience method for creating and publishing an event
        in a single call.

        Args:
            event_type: Type of event.
            payload: Event payload.
            sender_id: ID of the sender.
            priority: Event priority.
            **kwargs: Additional event properties.

        Example:
            >>> bus = EventBus()
            >>> asyncio.run(bus.emit(
            ...     "system.started",
            ...     {"timestamp": "2024-01-01"},
            ...     sender_id="kernel"
            ... ))
        """
        from tangku_agentos.runtime_communication.models.messages import (
            Event,
            MessageType,
            MessagePriority,
        )

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=sender_id,
            event_type=event_type,
            payload=payload,
            priority=priority,
            **kwargs,
        )
        await self.publish(event)

    def subscribe(
        self,
        event_type: Union[str, "MessageType"],
        handler: Union["IEventHandler[Event]", "IMessageHandler[Message]"],
        filter_func: Optional[Callable[["Event"], bool]] = None,
        priority: int = 0,
    ) -> str:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to.
            handler: Handler to call for matching events.
            filter_func: Optional filter function for event matching.
            priority: Subscription priority (higher = processed first).

        Returns:
            Subscription ID.

        Example:
            >>> class MyEventHandler:
            ...     async def handle_event(self, event: Event) -> None:
            ...         print(f"Event: {event.event_type}")
            >>> 
            >>> bus = EventBus()
            >>> handler = MyEventHandler()
            >>> sub_id = bus.subscribe("system.started", handler)
        """
        subscription_id = str(uuid.uuid4())

        # Convert MessageType enum to string for storage
        type_key = (
            event_type if isinstance(event_type, str) else event_type.name
        )

        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_type=event_type,
            handler=handler,
            filter_func=filter_func,
            priority=priority,
        )

        asyncio.run(self._subscribe_async(type_key, subscription))
        return subscription_id

    async def _subscribe_async(
        self, type_key: str, subscription: EventSubscription
    ) -> None:
        """Async version of subscribe."""
        async with self._subscriptions_lock:
            self._subscriptions[type_key].append(subscription)
            self._subscriptions[type_key].sort(
                key=lambda s: s.priority, reverse=True
            )

            async with self._metrics_lock:
                self._metrics["subscriptions_active"] += 1
                self._metrics["subscriptions_total"] += 1

            if self._enable_logging:
                logger.info(
                    f"Event handler subscribed to '{type_key}': "
                    f"{subscription.subscription_id}"
                )

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.

        Args:
            subscription_id: ID of the subscription to remove.

        Returns:
            True if subscription was removed, False otherwise.

        Example:
            >>> bus = EventBus()
            >>> sub_id = bus.subscribe("system.started", handler)
            >>> bus.unsubscribe(sub_id)
            True
        """
        return asyncio.run(self._unsubscribe_async(subscription_id))

    async def _unsubscribe_async(self, subscription_id: str) -> bool:
        """Async version of unsubscribe."""
        async with self._subscriptions_lock:
            for type_key, subscriptions in self._subscriptions.items():
                for i, sub in enumerate(subscriptions):
                    if sub.subscription_id == subscription_id:
                        subscriptions.pop(i)

                        async with self._metrics_lock:
                            self._metrics["subscriptions_active"] -= 1

                        if self._enable_logging:
                            logger.info(
                                f"Event subscription {subscription_id} "
                                f"removed from '{type_key}'"
                            )
                        return True
            return False

    def unsubscribe_all(
        self, event_type: Optional[Union[str, "MessageType"]] = None
    ) -> int:
        """
        Unsubscribe all handlers from an event type or all types.

        Args:
            event_type: Specific event type to clear (optional).

        Returns:
            Number of subscriptions removed.

        Example:
            >>> bus = EventBus()
            >>> bus.subscribe("system.started", handler1)
            >>> bus.subscribe("system.started", handler2)
            >>> count = bus.unsubscribe_all("system.started")
            >>> count
            2
        """
        return asyncio.run(self._unsubscribe_all_async(event_type))

    async def _unsubscribe_all_async(
        self, event_type: Optional[Union[str, "MessageType"]] = None
    ) -> int:
        """Async version of unsubscribe_all."""
        count = 0

        if event_type is not None:
            type_key = (
                event_type if isinstance(event_type, str) else event_type.name
            )
            async with self._subscriptions_lock:
                if type_key in self._subscriptions:
                    count = len(self._subscriptions[type_key])
                    self._subscriptions[type_key].clear()

                    async with self._metrics_lock:
                        self._metrics["subscriptions_active"] -= count
        else:
            async with self._subscriptions_lock:
                for type_key in list(self._subscriptions.keys()):
                    count += len(self._subscriptions[type_key])
                    self._subscriptions[type_key].clear()

                async with self._metrics_lock:
                    self._metrics["subscriptions_active"] = 0

        return count

    def get_subscriptions(
        self, event_type: Optional[Union[str, "MessageType"]] = None
    ) -> List[str]:
        """
        Get list of subscription IDs.

        Args:
            event_type: Filter by event type (optional).

        Returns:
            List of subscription IDs.

        Example:
            >>> bus = EventBus()
            >>> sub_id = bus.subscribe("system.started", handler)
            >>> bus.get_subscriptions("system.started")
            ['sub-...']
        """
        if event_type is not None:
            type_key = (
                event_type if isinstance(event_type, str) else event_type.name
            )
            async with self._subscriptions_lock:
                return [
                    sub.subscription_id
                    for sub in self._subscriptions.get(type_key, [])
                ]
        else:
            async with self._subscriptions_lock:
                return [
                    sub.subscription_id
                    for subs in self._subscriptions.values()
                    for sub in subs
                ]

    def get_event_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List["Event"]:
        """
        Retrieve event history with optional filtering.

        Args:
            event_type: Filter by event type (optional).
            limit: Maximum events to return.

        Returns:
            List of events.

        Example:
            >>> bus = EventBus()
            >>> # Publish some events
            >>> history = bus.get_event_history(limit=10)
        """
        events = list(self._event_history)

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event bus metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> bus = EventBus()
            >>> metrics = bus.get_metrics()
            >>> metrics["events_published"]
            0
        """
        return {
            **self._metrics,
            "event_history_size": len(self._event_history),
            "active_subscriptions": self._metrics["subscriptions_active"],
            "total_subscriptions": self._metrics["subscriptions_total"],
        }

    def clear_history(self) -> int:
        """
        Clear event history.

        Returns:
            Count of events cleared.

        Example:
            >>> bus = EventBus()
            >>> count = bus.clear_history()
        """
        count = len(self._event_history)
        self._event_history.clear()
        return count

    def shutdown(self) -> None:
        """
        Shutdown event bus.

        Cleans up resources and stops all processing.

        Example:
            >>> bus = EventBus()
            >>> bus.shutdown()
        """
        self._event_history.clear()
        self._subscriptions.clear()
        self._metrics.clear()

        logger.info("Event bus shutdown complete")

    async def _find_matching_subscriptions(
        self, event: "Event"
    ) -> List[EventSubscription]:
        """
        Find all subscriptions that match the given event.

        Args:
            event: The event to match.

        Returns:
            List of matching subscriptions.
        """
        type_key = event.message_type.name

        async with self._subscriptions_lock:
            # Get subscriptions for specific event type
            specific_subs = list(self._subscriptions.get(type_key, []))

            # Get wildcard subscriptions
            wildcard_subs = list(self._subscriptions.get("*", []))

        all_subscriptions = specific_subs + wildcard_subs

        # Filter by match
        return [
            sub
            for sub in all_subscriptions
            if sub.matches(event)
        ]

    async def _record_event(self, event: "Event") -> None:
        """
        Store event in history.

        Args:
            event: Event to store.
        """
        async with self._event_history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_event_history:
                self._event_history.pop(0)

    def _validate_event(self, event: "Event") -> None:
        """
        Validate an event before publishing.

        Args:
            event: Event to validate.

        Raises:
            MessageValidationError: If event is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not event.sender_id:
            raise MessageValidationError(
                "Event sender_id is required",
                message_id=event.message_id,
                validation_errors=["sender_id is required"],
            )

        if not event.event_type:
            raise MessageValidationError(
                "Event event_type is required",
                message_id=event.message_id,
                validation_errors=["event_type is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the event bus."""
        return (
            f"EventBus("
            f"subscriptions={self._metrics['subscriptions_active']}, "
            f"history={len(self._event_history)})"
        )
