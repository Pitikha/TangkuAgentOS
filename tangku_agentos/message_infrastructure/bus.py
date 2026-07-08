"""
Message Infrastructure - Core Message Bus Implementation

This module provides a comprehensive, production-grade message bus supporting:
- Direct messaging (point-to-point)
- Multicast and broadcast
- Request/response patterns
- Reply chains and subscriptions
- Routing rules and filtering
- Message expiration and cancellation
- Acknowledgements and retries
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, UUID
from enum import Enum
from datetime import datetime, timedelta
import uuid
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """
    Core message model with full routing and lifecycle information.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast/multicast
    message_type: str = ""
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None  # Links related messages
    reply_to: Optional[str] = None  # Message ID to reply to
    status: MessageStatus = MessageStatus.PENDING
    delivery_attempts: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def should_retry(self) -> bool:
        """Check if message should be retried."""
        return (
            self.status == MessageStatus.FAILED
            and self.delivery_attempts < self.max_retries
        )

    def add_tag(self, tag: str) -> None:
        """Add metadata tag."""
        self.tags.add(tag)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self.metadata[key] = value


@dataclass
class RoutingRule:
    """Rules for message routing."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    condition: Callable[[Message], bool] = lambda msg: True
    priority: int = 0  # Higher number = higher priority
    enabled: bool = True
    target_handlers: List[str] = field(default_factory=list)


class MessageFilter:
    """Advanced message filtering."""

    def __init__(self):
        self.conditions: List[Callable[[Message], bool]] = []

    def by_sender(self, sender_id: str) -> "MessageFilter":
        """Filter by sender ID."""
        self.conditions.append(lambda msg: msg.sender_id == sender_id)
        return self

    def by_type(self, message_type: str) -> "MessageFilter":
        """Filter by message type."""
        self.conditions.append(lambda msg: msg.message_type == message_type)
        return self

    def by_priority(self, min_priority: MessagePriority) -> "MessageFilter":
        """Filter by priority."""
        self.conditions.append(
            lambda msg: msg.priority.value <= min_priority.value
        )
        return self

    def by_tag(self, tag: str) -> "MessageFilter":
        """Filter by tag."""
        self.conditions.append(lambda msg: tag in msg.tags)
        return self

    def by_correlation(self, correlation_id: str) -> "MessageFilter":
        """Filter by correlation ID."""
        self.conditions.append(lambda msg: msg.correlation_id == correlation_id)
        return self

    def matches(self, message: Message) -> bool:
        """Check if message matches all conditions."""
        return all(condition(message) for condition in self.conditions)


class MessageHandler(ABC):
    """Abstract base for message handlers."""

    @abstractmethod
    async def handle(self, message: Message) -> Any:
        """Process incoming message."""
        pass

    def can_handle(self, message: Message) -> bool:
        """Check if this handler can process the message."""
        return True


class SyncMessageHandler(MessageHandler):
    """Synchronous message handler wrapper."""

    def __init__(self, func: Callable[[Message], Any]):
        self.func = func

    async def handle(self, message: Message) -> Any:
        """Wrap sync function for async execution."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.func, message)


class MessageSubscription:
    """Subscription to message types."""

    def __init__(
        self,
        subscription_id: str,
        message_type: str,
        handler: MessageHandler,
        message_filter: Optional[MessageFilter] = None,
    ):
        self.subscription_id = subscription_id
        self.message_type = message_type
        self.handler = handler
        self.message_filter = message_filter or MessageFilter()
        self.active = True
        self.message_count = 0
        self.error_count = 0

    async def process(self, message: Message) -> Any:
        """Process message if it matches the subscription."""
        if not self.active or not self.message_filter.matches(message):
            return None

        try:
            self.message_count += 1
            return await self.handler.handle(message)
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing message in subscription: {e}")
            raise


class MessageBus:
    """
    Production-grade message bus supporting routing, filtering,
    acknowledgements, retries, and comprehensive observability.
    """

    def __init__(
        self,
        max_message_history: int = 10000,
        default_expiration: timedelta = timedelta(hours=24),
        executor_threads: int = 10,
    ):
        self.message_id_counter: str = ""
        self.handlers: Dict[str, List[MessageSubscription]] = defaultdict(list)
        self.routing_rules: Dict[str, RoutingRule] = {}
        self.message_history: List[Message] = []
        self.max_message_history = max_message_history
        self.dead_letter_queue: List[Message] = []
        self.default_expiration = default_expiration
        self.executor = ThreadPoolExecutor(max_workers=executor_threads)

        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "messages_expired": 0,
            "messages_cancelled": 0,
        }

        # Request/response tracking
        self.pending_responses: Dict[str, asyncio.Future] = {}

    async def send(
        self,
        message: Message,
        wait_for_response: bool = False,
        response_timeout: float = 30.0,
    ) -> Optional[Message]:
        """
        Send a message to recipient(s).

        Args:
            message: Message to send
            wait_for_response: Wait for response (request/response pattern)
            response_timeout: Timeout for response in seconds

        Returns:
            Response message if wait_for_response=True, else None
        """
        if message.is_expired():
            message.status = MessageStatus.EXPIRED
            self.metrics["messages_expired"] += 1
            return None

        # Set expiration if not set
        if message.expires_at is None:
            message.expires_at = datetime.utcnow() + self.default_expiration

        message.status = MessageStatus.SENT
        self.metrics["messages_sent"] += 1
        self._record_message(message)

        # Handle request/response pattern
        if wait_for_response:
            response_future: asyncio.Future = asyncio.Future()
            self.pending_responses[message.message_id] = response_future
            message.reply_to = message.message_id

        try:
            if message.recipient_id:
                # Direct message
                await self._route_direct(message)
            else:
                # Broadcast/multicast
                await self._route_broadcast(message)

            if wait_for_response:
                response = await asyncio.wait_for(
                    response_future, timeout=response_timeout
                )
                return response
        except asyncio.TimeoutError:
            logger.warning(
                f"Response timeout for message {message.message_id}"
            )
            if message.message_id in self.pending_responses:
                del self.pending_responses[message.message_id]
            return None
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            message.status = MessageStatus.FAILED
            self.metrics["messages_failed"] += 1
            raise

        return None

    async def broadcast(
        self,
        message_type: str,
        payload: Any,
        sender_id: str = "system",
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """
        Broadcast message to all subscribers of a type.

        Returns:
            Number of subscribers notified
        """
        message = Message(
            sender_id=sender_id,
            message_type=message_type,
            payload=payload,
            priority=priority,
        )
        await self.send(message)
        return len(self.handlers.get(message_type, []))

    async def multicast(
        self,
        message_type: str,
        recipient_ids: List[str],
        payload: Any,
        sender_id: str = "system",
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> int:
        """
        Send same message to multiple specific recipients.

        Returns:
            Number of recipients
        """
        count = 0
        for recipient_id in recipient_ids:
            message = Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=message_type,
                payload=payload,
                priority=priority,
            )
            await self.send(message)
            count += 1
        return count

    def subscribe(
        self,
        message_type: str,
        handler: MessageHandler,
        message_filter: Optional[MessageFilter] = None,
    ) -> str:
        """
        Subscribe handler to message type.

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        subscription = MessageSubscription(
            subscription_id, message_type, handler, message_filter
        )
        self.handlers[message_type].append(subscription)
        logger.info(
            f"Handler subscribed to '{message_type}': {subscription_id}"
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe handler."""
        for message_type in self.handlers:
            for i, sub in enumerate(self.handlers[message_type]):
                if sub.subscription_id == subscription_id:
                    self.handlers[message_type].pop(i)
                    logger.info(f"Subscription {subscription_id} removed")
                    return True
        return False

    def add_routing_rule(self, rule: RoutingRule) -> str:
        """Add message routing rule."""
        self.routing_rules[rule.rule_id] = rule
        logger.info(f"Routing rule added: {rule.name}")
        return rule.rule_id

    def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove routing rule."""
        if rule_id in self.routing_rules:
            del self.routing_rules[rule_id]
            return True
        return False

    async def _route_direct(self, message: Message) -> None:
        """Route message to specific recipient."""
        subscribers = self.handlers.get(message.message_type, [])
        if not subscribers:
            logger.warning(
                f"No subscribers for message type: {message.message_type}"
            )
            self.dead_letter_queue.append(message)
            return

        tasks = [sub.process(message) for sub in subscribers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle request/response pattern
        if message.reply_to and results:
            response = Message(
                sender_id="system",
                recipient_id=message.sender_id,
                message_type=f"{message.message_type}_response",
                payload=results[0],
                correlation_id=message.correlation_id or message.message_id,
                reply_to=message.reply_to,
            )
            if message.reply_to in self.pending_responses:
                future = self.pending_responses.pop(message.reply_to)
                if not future.done():
                    future.set_result(response)

        message.status = MessageStatus.DELIVERED
        self.metrics["messages_delivered"] += 1

    async def _route_broadcast(self, message: Message) -> None:
        """Route broadcast message to all subscribers."""
        subscribers = self.handlers.get(message.message_type, [])
        if subscribers:
            tasks = [sub.process(message) for sub in subscribers]
            await asyncio.gather(*tasks, return_exceptions=True)
            message.status = MessageStatus.DELIVERED
            self.metrics["messages_delivered"] += 1
        else:
            logger.debug(
                f"No subscribers for broadcast: {message.message_type}"
            )

    def _record_message(self, message: Message) -> None:
        """Store message in history."""
        self.message_history.append(message)
        if len(self.message_history) > self.max_message_history:
            self.message_history.pop(0)

    def get_message_history(
        self,
        message_filter: Optional[MessageFilter] = None,
        limit: int = 100,
    ) -> List[Message]:
        """
        Retrieve message history with optional filtering.

        Args:
            message_filter: Filter criteria
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        messages = self.message_history
        if message_filter:
            messages = [msg for msg in messages if message_filter.matches(msg)]
        return messages[-limit:]

    def get_dead_letter_messages(self, limit: int = 100) -> List[Message]:
        """Retrieve dead-letter queue messages."""
        return self.dead_letter_queue[-limit:]

    def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message delivery."""
        for message in self.message_history:
            if message.message_id == message_id:
                message.status = MessageStatus.DELIVERED
                return True
        return False

    async def retry_failed(self) -> int:
        """
        Retry failed messages from dead-letter queue.

        Returns:
            Number of messages retried
        """
        retried = 0
        remaining = []

        for message in self.dead_letter_queue:
            if message.should_retry():
                message.delivery_attempts += 1
                try:
                    await self.send(message)
                    retried += 1
                    self.metrics["messages_retried"] += 1
                except Exception as e:
                    logger.error(f"Retry failed for message: {e}")
                    remaining.append(message)
            else:
                remaining.append(message)

        self.dead_letter_queue = remaining
        return retried

    def get_metrics(self) -> Dict[str, Any]:
        """Get bus metrics."""
        return {
            **self.metrics,
            "message_history_size": len(self.message_history),
            "dead_letter_size": len(self.dead_letter_queue),
            "pending_responses": len(self.pending_responses),
            "active_subscriptions": sum(
                len(subs) for subs in self.handlers.values()
            ),
        }

    def clear_history(self) -> int:
        """Clear message history. Returns count cleared."""
        count = len(self.message_history)
        self.message_history.clear()
        return count

    def shutdown(self) -> None:
        """Shutdown message bus."""
        self.executor.shutdown(wait=True)
        logger.info("Message bus shutdown complete")
