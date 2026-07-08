"""
Runtime Communication Framework - Core Message Bus Implementation

This module provides a comprehensive, production-grade message bus supporting:
- Direct messaging (point-to-point)
- Multicast and broadcast
- Request/response patterns
- Reply chains and subscriptions
- Routing rules and filtering
- Message expiration and cancellation
- Acknowledgements and retries
- Middleware pipeline
- Interceptors
- Tracing and structured logging
- Metrics collection

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
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

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        MessageType,
        MessagePriority,
        MessageStatus,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IMessageBus,
        IMessageHandler,
        IMiddleware,
        IMessageInterceptor,
    )

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """
    Represents a subscription to a specific message type.

    A subscription binds a message handler to a message type with optional
    filtering. When a message of the subscribed type is published, the handler
    is invoked if the message passes the filter.

    Attributes:
        subscription_id: Unique identifier for the subscription.
        message_type: Type of message to subscribe to (string or MessageType enum).
        handler: Handler function to call for matching messages.
        filter_func: Optional filter function for message matching.
        priority: Subscription priority (higher = processed first).
        active: Whether the subscription is active.
        message_count: Number of messages processed by this subscription.
        error_count: Number of errors during processing.
    """

    subscription_id: str
    message_type: Union[str, "MessageType"]
    handler: "IMessageHandler[Message]"
    filter_func: Optional[Callable[["Message"], bool]] = None
    priority: int = 0
    active: bool = True
    message_count: int = 0
    error_count: int = 0

    def matches(self, message: "Message") -> bool:
        """
        Check if this subscription matches the given message.

        Args:
            message: The message to check.

        Returns:
            True if the subscription matches, False otherwise.
        """
        if not self.active:
            return False

        # Check message type
        message_type_name = message.message_type.name
        sub_type = (
            self.message_type
            if isinstance(self.message_type, str)
            else self.message_type.name
        )

        if message_type_name != sub_type and sub_type != "*":
            return False

        # Check filter function
        if self.filter_func is not None:
            try:
                return self.filter_func(message)
            except Exception as e:
                logger.error(f"Error in subscription filter: {e}")
                return False

        return True

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
class RoutingRule:
    """
    Defines a routing rule for message delivery.

    Routing rules allow dynamic message routing based on message content,
    metadata, or other criteria. Rules are evaluated in priority order.

    Attributes:
        rule_id: Unique identifier for the rule.
        name: Human-readable name for the rule.
        condition: Function to determine if rule applies to a message.
        priority: Rule priority (higher = evaluated first).
        enabled: Whether the rule is active.
        target_handlers: List of handler IDs to route to.
        transform: Optional function to transform the message before delivery.
    """

    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    condition: Callable[["Message"], bool] = lambda msg: True
    priority: int = 0
    enabled: bool = True
    target_handlers: List[str] = field(default_factory=list)
    transform: Optional[Callable[["Message"], "Message"]] = None

    def applies_to(self, message: "Message") -> bool:
        """
        Check if this rule applies to the given message.

        Args:
            message: The message to check.

        Returns:
            True if rule applies, False otherwise.
        """
        if not self.enabled:
            return False
        try:
            return self.condition(message)
        except Exception as e:
            logger.error(f"Error evaluating routing rule {self.name}: {e}")
            return False
