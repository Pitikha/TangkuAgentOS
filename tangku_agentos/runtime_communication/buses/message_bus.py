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
)

from tangku_agentos.runtime_communication.models.messages import (
    Message,
    MessageType,
    MessagePriority,
    MessageStatus,
)
from tangku_agentos.runtime_communication.models.exceptions import (
    MessageError,
    MessageDeliveryError,
    MessageTimeoutError,
    MessageValidationError,
    RuntimeNotFoundError,
    RuntimeNotAvailableError,
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
    """Represents a subscription to a specific message type."""
    
    subscription_id: str
    message_type: Union[str, MessageType]
    handler: IMessageHandler[Message]
    filter_func: Optional[Callable[[Message], bool]] = None
    priority: int = 0
    active: bool = True
    message_count: int = 0
    error_count: int = 0
    
    def matches(self, message: Message) -> bool:
        """Check if this subscription matches the given message."""
        if not self.active:
            return False
        
        type_key = message.message_type.name
        sub_type = self.message_type if isinstance(self.message_type, str) else self.message_type.name
        
        if type_key != sub_type and sub_type != "*":
            return False
        
        if self.filter_func is not None:
            try:
                return self.filter_func(message)
            except Exception as e:
                logger.error(f"Error in subscription filter: {e}")
                return False
        
        return True
    
    async def process(self, message: Message) -> Any:
        """Process a message with this subscription."""
        if not self.active:
            return None
        
        self.message_count += 1
        try:
            return await self.handler.handle(message)
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing message in subscription {self.subscription_id}: {e}")
            raise


@dataclass
class RoutingRule:
    """Defines a routing rule for message delivery."""
    
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    condition: Callable[[Message], bool] = lambda msg: True
    priority: int = 0
    enabled: bool = True
    target_handlers: List[str] = field(default_factory=list)
    transform: Optional[Callable[[Message], Message]] = None
    
    def applies_to(self, message: Message) -> bool:
        """Check if this rule applies to the given message."""
        if not self.enabled:
            return False
        try:
            return self.condition(message)
        except Exception as e:
            logger.error(f"Error evaluating routing rule {self.name}: {e}")
            return False
