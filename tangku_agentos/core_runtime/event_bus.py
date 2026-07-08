from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from threading import RLock
from typing import (
    Any,
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from .constants import EventPriority
from .exceptions import (
    DeadLetterQueueError,
    EventBusError,
    EventHandlerError,
    MiddlewareError,
)
from .types import (
    AsyncEventHandler,
    AsyncMiddleware,
    EventHandler,
    EventPayload,
    EventRecord,
    Middleware,
)


@dataclass
class EventMetrics:
    """Metrics for event bus operations."""

    events_published: int = 0
    events_failed: int = 0
    events_replayed: int = 0
    dlq_size: int = 0
    last_event_time: float = 0.0


@dataclass
class DeadLetterQueueEntry:
    """Represents a failed event in the DLQ."""

    event_name: str
    payload: EventPayload
    timestamp: float
    error: Exception
    retries: int = 0


class EventBus:
    """
    Production-grade event bus with:
    - Thread-safe and async publishing
    - Event priorities
    - Event filtering
    - Middleware support
    - Event metrics
    - Dead-letter queue (DLQ)
    - Event replay
    """

    def __init__(self) -> None:
        self._listeners: DefaultDict[str, List[Tuple[EventHandler, EventPriority]]] = defaultdict(list)
        self._async_listeners: DefaultDict[str, List[Tuple[AsyncEventHandler, EventPriority]]] = defaultdict(list)
        self._middleware: List[Middleware] = []
        self._async_middleware: List[AsyncMiddleware] = []
        self._history: List[EventRecord] = []
        self._dlq: List[DeadLetterQueueEntry] = []
        self._metrics = EventMetrics()
        self._lock = RLock()
        self._filters: DefaultDict[str, List[Callable[[EventPayload], bool]]] = defaultdict(list)

    # --- Listener Management ---
    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Subscribe a synchronous handler to an event with a priority."""
        if not event_name or not callable(handler):
            raise EventBusError("Event name and handler must be valid.")

        with self._lock:
            self._listeners[event_name].append((handler, priority))
            self._listeners[event_name].sort(key=lambda x: x[1], reverse=True)

    def subscribe_async(
        self,
        event_name: str,
        handler: AsyncEventHandler,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """Subscribe an async handler to an event with a priority."""
        if not event_name or not callable(handler):
            raise EventBusError("Event name and async handler must be valid.")

        with self._lock:
            self._async_listeners[event_name].append((handler, priority))
            self._async_listeners[event_name].sort(key=lambda x: x[1], reverse=True)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribe a synchronous handler from an event."""
        with self._lock:
            self._listeners[event_name] = [
                (h, p) for h, p in self._listeners[event_name] if h != handler
            ]

    def unsubscribe_async(self, event_name: str, handler: AsyncEventHandler) -> None:
        """Unsubscribe an async handler from an event."""
        with self._lock:
            self._async_listeners[event_name] = [
                (h, p) for h, p in self._async_listeners[event_name] if h != handler
            ]

    # --- Filter Management ---
    def add_filter(
        self, event_name: str, filter_func: Callable[[EventPayload], bool]
    ) -> None:
        """Add a filter for an event."""
        with self._lock:
            self._filters[event_name].append(filter_func)

    def remove_filter(
        self, event_name: str, filter_func: Callable[[EventPayload], bool]
    ) -> None:
        """Remove a filter for an event."""
        with self._lock:
            self._filters[event_name] = [
                f for f in self._filters[event_name] if f != filter_func
            ]

    # --- Middleware Management ---
    def add_middleware(self, middleware: Middleware) -> None:
        """Add a synchronous middleware."""
        if not callable(middleware):
            raise MiddlewareError("Middleware must be callable.")
        with self._lock:
            self._middleware.append(middleware)

    def add_async_middleware(self, middleware: AsyncMiddleware) -> None:
        """Add an async middleware."""
        if not callable(middleware):
            raise MiddlewareError("Async middleware must be callable.")
        with self._lock:
            self._async_middleware.append(middleware)

    # --- Publishing ---
    def publish(
        self,
        event_name: str,
        payload: EventPayload | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> EventRecord:
        """
        Publish an event synchronously.
        Applies middleware, filters, and handles failures via DLQ.
        """
        if not event_name:
            raise EventBusError("Event name must be provided.")

        payload = payload or EventPayload()
        record = EventRecord(
            name=event_name,
            payload=payload,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        with self._lock:
            self._history.append(record)
            self._metrics.events_published += 1
            self._metrics.last_event_time = record.timestamp

        # Apply filters
        filters = self._filters.get(event_name, [])
        for filter_func in filters:
            if not filter_func(payload):
                return record

        # Apply middleware
        def build_middleware_chain(
            middleware_list: List[Middleware],
            handlers: List[Tuple[EventHandler, EventPriority]],
        ) -> Callable[[], None]:
            if not middleware_list:
                return lambda: self._execute_handlers(handlers, event_name, payload, record)

            middleware = middleware_list[0]
            next_chain = build_middleware_chain(middleware_list[1:], handlers)

            def chain():
                middleware(event_name, payload, next_chain)

            return chain

        # Execute sync handlers
        handlers = self._listeners.get(event_name, [])
        if handlers:
            try:
                middleware_chain = build_middleware_chain(self._middleware, handlers)
                middleware_chain()
            except Exception as e:
                self._add_to_dlq(event_name, payload, e)

        # Execute async handlers in a new event loop (non-blocking)
        async_handlers = self._async_listeners.get(event_name, [])
        if async_handlers:
            asyncio.create_task(self._execute_async_handlers(async_handlers, event_name, payload, record))

        return record

    async def publish_async(
        self,
        event_name: str,
        payload: EventPayload | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> EventRecord:
        """
        Publish an event asynchronously.
        Applies async middleware, filters, and handles failures via DLQ.
        """
        if not event_name:
            raise EventBusError("Event name must be provided.")

        payload = payload or EventPayload()
        record = EventRecord(
            name=event_name,
            payload=payload,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        with self._lock:
            self._history.append(record)
            self._metrics.events_published += 1
            self._metrics.last_event_time = record.timestamp

        # Apply filters
        filters = self._filters.get(event_name, [])
        for filter_func in filters:
            if not filter_func(payload):
                return record

        # Apply async middleware
        async def build_async_middleware_chain(
            middleware_list: List[AsyncMiddleware],
            handlers: List[Tuple[AsyncEventHandler, EventPriority]],
        ) -> Callable[[], Awaitable[None]]:
            if not middleware_list:
                return lambda: self._execute_async_handlers(handlers, event_name, payload, record)

            middleware = middleware_list[0]
            next_chain = await build_async_middleware_chain(middleware_list[1:], handlers)

            async def chain():
                await middleware(event_name, payload, next_chain)

            return chain

        # Execute async handlers
        handlers = self._async_listeners.get(event_name, [])
        if handlers:
            try:
                middleware_chain = await build_async_middleware_chain(self._async_middleware, handlers)
                await middleware_chain()
            except Exception as e:
                self._add_to_dlq(event_name, payload, e)

        return record

    # --- Helper Methods ---
    def _execute_handlers(
        self,
        handlers: List[Tuple[EventHandler, EventPriority]],
        event_name: str,
        payload: EventPayload,
        record: EventRecord,
    ) -> None:
        """Execute synchronous handlers for an event."""
        errors: List[Exception] = []
        for handler, _ in handlers:
            try:
                handler(event_name, payload)
            except Exception as e:
                errors.append(e)

        if errors:
            self._add_to_dlq(event_name, payload, EventHandlerError(f"{len(errors)} handlers failed"))

    async def _execute_async_handlers(
        self,
        handlers: List[Tuple[AsyncEventHandler, EventPriority]],
        event_name: str,
        payload: EventPayload,
        record: EventRecord,
    ) -> None:
        """Execute asynchronous handlers for an event."""
        errors: List[Exception] = []
        for handler, _ in handlers:
            try:
                await handler(event_name, payload)
            except Exception as e:
                errors.append(e)

        if errors:
            self._add_to_dlq(event_name, payload, EventHandlerError(f"{len(errors)} async handlers failed"))

    def _add_to_dlq(self, event_name: str, payload: EventPayload, error: Exception) -> None:
        """Add a failed event to the dead-letter queue."""
        with self._lock:
            self._dlq.append(
                DeadLetterQueueEntry(
                    event_name=event_name,
                    payload=payload,
                    timestamp=time.time(),
                    error=error,
                )
            )
            self._metrics.events_failed += 1
            self._metrics.dlq_size += 1

    # --- Replay ---
    def replay_events(
        self,
        event_names: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> int:
        """
        Replay events from history.
        Returns the number of events replayed.
        """
        with self._lock:
            events_to_replay = []
            for record in self._history:
                if event_names and record.name not in event_names:
                    continue
                if start_time and record.timestamp < start_time:
                    continue
                if end_time and record.timestamp > end_time:
                    continue
                events_to_replay.append(record)

        replayed = 0
        for record in events_to_replay:
            try:
                self.publish(record.name, record.payload, record.metadata)
                replayed += 1
            except Exception as e:
                self._add_to_dlq(record.name, record.payload, e)

        with self._lock:
            self._metrics.events_replayed += replayed

        return replayed

    # --- DLQ Management ---
    def get_dlq(self) -> List[DeadLetterQueueEntry]:
        """Get all entries in the dead-letter queue."""
        with self._lock:
            return list(self._dlq)

    def retry_dlq_entry(self, index: int) -> bool:
        """Retry a specific DLQ entry. Returns True if successful."""
        with self._lock:
            if index >= len(self._dlq):
                raise DeadLetterQueueError("Invalid DLQ index.")
            entry = self._dlq[index]

        try:
            self.publish(entry.event_name, entry.payload)
            with self._lock:
                self._dlq.pop(index)
                self._metrics.dlq_size -= 1
            return True
        except Exception as e:
            with self._lock:
                entry.retries += 1
                entry.error = e
            return False

    def clear_dlq(self) -> None:
        """Clear the dead-letter queue."""
        with self._lock:
            self._dlq.clear()
            self._metrics.dlq_size = 0

    # --- Metrics ---
    def get_metrics(self) -> EventMetrics:
        """Get event bus metrics."""
        with self._lock:
            return EventMetrics(
                events_published=self._metrics.events_published,
                events_failed=self._metrics.events_failed,
                events_replayed=self._metrics.events_replayed,
                dlq_size=self._metrics.dlq_size,
                last_event_time=self._metrics.last_event_time,
            )

    # --- History ---
    def history(self) -> List[EventRecord]:
        """Get all recorded events."""
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._history.clear()

    # --- Listener Management ---
    def list_listeners(self, event_name: str) -> List[EventHandler]:
        """List all synchronous listeners for an event."""
        with self._lock:
            return [handler for handler, _ in self._listeners.get(event_name, [])]

    def list_async_listeners(self, event_name: str) -> List[AsyncEventHandler]:
        """List all async listeners for an event."""
        with self._lock:
            return [handler for handler, _ in self._async_listeners.get(event_name, [])]

    def clear_listeners(self) -> None:
        """Clear all listeners."""
        with self._lock:
            self._listeners.clear()
            self._async_listeners.clear()
