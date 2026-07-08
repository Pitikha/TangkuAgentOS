"""
Runtime Communication Framework - Memory Runtime Integration Example

This module provides an example of how to integrate the Memory Runtime
with the Runtime Communication Framework.

This example demonstrates:
1. Inheriting from BaseRuntime
2. Implementing required lifecycle methods
3. Registering command and query handlers
4. Publishing events
5. Using standard system commands and queries

Example usage:
    from tangku_agentos.runtime_communication.integration.examples.memory_runtime_example import MemoryRuntimeExample
    from tangku_agentos.runtime_communication.integration import create_runtime_config
    
    # Create configuration
    config = create_runtime_config(
        runtime_id="memory_runtime",
        name="Memory Runtime",
        version="1.0.0",
        description="Manages memory storage and retrieval",
        capabilities={"memory", "storage", "persistence"},
    )
    
    # Create and start the runtime
    memory_runtime = MemoryRuntimeExample(config)
    await memory_runtime.initialize()
    await memory_runtime.start()
    
    # The runtime is now ready to handle commands and queries
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.integration.base import RuntimeConfig
    from tangku_agentos.runtime_communication.models.messages import Command, Query, Event

logger = logging.getLogger(__name__)


class MemoryRuntimeExample:
    """
    Example integration of Memory Runtime with Runtime Communication Framework.

    This class demonstrates how to integrate an existing memory runtime
    with the new communication framework.

    Features:
    - Inherits from BaseRuntime for full integration
    - Implements command handlers for memory operations
    - Implements query handlers for memory queries
    - Publishes memory events
    - Uses standard system commands and queries

    Example:
        >>> from tangku_agentos.runtime_communication.integration import (
        ...     BaseRuntime,
        ...     create_runtime_config,
        ...     create_runtime_capabilities,
        ... )
        >>> 
        >>> config = create_runtime_config(
        ...     runtime_id="memory_runtime",
        ...     name="Memory Runtime",
        ...     capabilities={"memory", "storage"},
        ... )
        >>> 
        >>> runtime = MemoryRuntimeExample(config)
        >>> await runtime.initialize()
        >>> await runtime.start()
    """

    def __init__(self, config: "RuntimeConfig"):
        """
        Initialize the Memory Runtime Example.

        Args:
            config: Runtime configuration.
        """
        from tangku_agentos.runtime_communication.integration import (
            BaseRuntime,
            create_runtime_capabilities,
        )

        # Define capabilities
        capabilities = create_runtime_capabilities(
            can_handle_commands=True,
            can_handle_queries=True,
            can_publish_events=True,
            can_subscribe_events=True,
            can_broadcast=True,
            supports_health_checks=True,
            supports_metrics=True,
            supports_tracing=True,
        )

        # Initialize base runtime
        super(MemoryRuntimeExample, self).__init__(config, capabilities)

        # Memory storage
        self._memory_store: Dict[str, Any] = {}
        self._memory_metadata: Dict[str, Dict[str, Any]] = {}

        # Command handlers
        self._command_handlers = {
            "save": self._handle_save_command,
            "load": self._handle_load_command,
            "delete": self._handle_delete_command,
            "update": self._handle_update_command,
            "clear": self._handle_clear_command,
        }

        # Query handlers
        self._query_handlers = {
            "get": self._handle_get_query,
            "search": self._handle_search_query,
            "list": self._handle_list_query,
            "exists": self._handle_exists_query,
            "count": self._handle_count_query,
        }

        logger.info(f"MemoryRuntimeExample initialized: {config.runtime_id}")

    async def _initialize(self) -> None:
        """
        Initialize the memory runtime.

        This method is called during runtime initialization.
        """
        logger.info(f"Initializing MemoryRuntimeExample: {self.runtime_id}")

        # Initialize memory storage
        self._memory_store = {}
        self._memory_metadata = {}

        # Register command handlers with the base runtime
        for command_type, handler in self._command_handlers.items():
            self.register_command_handler(command_type, handler)

        # Register query handlers with the base runtime
        for query_type, handler in self._query_handlers.items():
            self.register_query_handler(query_type, handler)

        # Register event handlers
        self.register_event_handler("memory.save", self._handle_memory_save_event)
        self.register_event_handler("memory.delete", self._handle_memory_delete_event)

        logger.info(f"MemoryRuntimeExample initialized: {self.runtime_id}")

    async def _start(self) -> None:
        """
        Start the memory runtime.

        This method is called during runtime startup.
        """
        logger.info(f"Starting MemoryRuntimeExample: {self.runtime_id}")

        # Start any background tasks if needed
        # For memory runtime, there are no background tasks

        logger.info(f"MemoryRuntimeExample started: {self.runtime_id}")

    async def _stop(self) -> None:
        """
        Stop the memory runtime.

        This method is called during runtime shutdown.
        """
        logger.info(f"Stopping MemoryRuntimeExample: {self.runtime_id}")

        # Clean up resources
        self._memory_store.clear()
        self._memory_metadata.clear()

        logger.info(f"MemoryRuntimeExample stopped: {self.runtime_id}")

    # Command Handlers

    async def _handle_save_command(self, command: "Command") -> Any:
        """
        Handle save command.

        Args:
            command: Save command.

        Returns:
            Result of save operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        data = payload.get("data", {})
        metadata = payload.get("metadata", {})

        if not memory_id:
            raise ValueError("memory_id is required for save command")

        # Save to memory store
        self._memory_store[memory_id] = data
        self._memory_metadata[memory_id] = metadata

        # Publish memory saved event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.memory_saved(
            runtime_id=self.runtime_id,
            memory_id=memory_id,
            size=len(str(data)),
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Memory saved: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "size": len(str(data)),
        }

    async def _handle_load_command(self, command: "Command") -> Any:
        """
        Handle load command.

        Args:
            command: Load command.

        Returns:
            Result of load operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required for load command")

        if memory_id not in self._memory_store:
            raise ValueError(f"Memory not found: {memory_id}")

        data = self._memory_store[memory_id]
        metadata = self._memory_metadata.get(memory_id, {})

        logger.debug(f"Memory loaded: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "data": data,
            "metadata": metadata,
        }

    async def _handle_delete_command(self, command: "Command") -> Any:
        """
        Handle delete command.

        Args:
            command: Delete command.

        Returns:
            Result of delete operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        reason = payload.get("reason", "user_request")

        if not memory_id:
            raise ValueError("memory_id is required for delete command")

        if memory_id not in self._memory_store:
            raise ValueError(f"Memory not found: {memory_id}")

        # Delete from memory store
        del self._memory_store[memory_id]
        if memory_id in self._memory_metadata:
            del self._memory_metadata[memory_id]

        # Publish memory deleted event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.memory_deleted(
            runtime_id=self.runtime_id,
            memory_id=memory_id,
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Memory deleted: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "reason": reason,
        }

    async def _handle_update_command(self, command: "Command") -> Any:
        """
        Handle update command.

        Args:
            command: Update command.

        Returns:
            Result of update operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        updates = payload.get("updates", {})
        metadata_updates = payload.get("metadata_updates", {})

        if not memory_id:
            raise ValueError("memory_id is required for update command")

        if memory_id not in self._memory_store:
            raise ValueError(f"Memory not found: {memory_id}")

        # Update memory data
        self._memory_store[memory_id].update(updates)

        # Update memory metadata
        if memory_id in self._memory_metadata:
            self._memory_metadata[memory_id].update(metadata_updates)

        # Publish memory updated event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.memory_updated(
            runtime_id=self.runtime_id,
            operation="update",
            memory_id=memory_id,
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Memory updated: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "updated_fields": list(updates.keys()),
        }

    async def _handle_clear_command(self, command: "Command") -> Any:
        """
        Handle clear command.

        Args:
            command: Clear command.

        Returns:
            Result of clear operation.
        """
        payload = command.payload or {}
        filter = payload.get("filter", {})

        # Clear all memories or filtered memories
        if filter:
            # Filter memories
            to_delete = [
                mid for mid, meta in self._memory_metadata.items()
                if all(meta.get(k) == v for k, v in filter.items())
            ]
            for mid in to_delete:
                del self._memory_store[mid]
                del self._memory_metadata[mid]
        else:
            # Clear all
            self._memory_store.clear()
            self._memory_metadata.clear()

        logger.debug("Memory cleared")

        return {
            "success": True,
            "cleared_count": len(self._memory_store) if filter else len(to_delete) if filter else 0,
        }

    # Query Handlers

    async def _handle_get_query(self, query: "Query") -> Any:
        """
        Handle get query.

        Args:
            query: Get query.

        Returns:
            Result of get operation.
        """
        payload = query.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required for get query")

        if memory_id not in self._memory_store:
            return None

        data = self._memory_store[memory_id]
        metadata = self._memory_metadata.get(memory_id, {})

        logger.debug(f"Memory retrieved: {memory_id}")

        return {
            "memory_id": memory_id,
            "data": data,
            "metadata": metadata,
        }

    async def _handle_search_query(self, query: "Query") -> Any:
        """
        Handle search query.

        Args:
            query: Search query.

        Returns:
            Result of search operation.
        """
        payload = query.payload or {}
        search_query = payload.get("query", "")
        filter = payload.get("filter", {})
        limit = payload.get("limit", 10)

        # Search memories
        results = []
        for memory_id, data in self._memory_store.items():
            metadata = self._memory_metadata.get(memory_id, {})

            # Apply filter
            if filter and not all(metadata.get(k) == v for k, v in filter.items()):
                continue

            # Apply search query (simple string search)
            if search_query:
                data_str = str(data)
                metadata_str = str(metadata)
                if search_query.lower() not in (data_str.lower() + metadata_str.lower()):
                    continue

            results.append({
                "memory_id": memory_id,
                "data": data,
                "metadata": metadata,
            })

            if len(results) >= limit:
                break

        logger.debug(f"Memory search: {len(results)} results")

        return {
            "query": search_query,
            "filter": filter,
            "results": results,
            "count": len(results),
        }

    async def _handle_list_query(self, query: "Query") -> Any:
        """
        Handle list query.

        Args:
            query: List query.

        Returns:
            Result of list operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})
        limit = payload.get("limit", 100)

        # List memories
        results = []
        for memory_id, data in self._memory_store.items():
            metadata = self._memory_metadata.get(memory_id, {})

            # Apply filter
            if filter and not all(metadata.get(k) == v for k, v in filter.items()):
                continue

            results.append({
                "memory_id": memory_id,
                "size": len(str(data)),
                "metadata": metadata,
            })

            if len(results) >= limit:
                break

        logger.debug(f"Memory list: {len(results)} items")

        return {
            "memories": results,
            "count": len(results),
            "total": len(self._memory_store),
        }

    async def _handle_exists_query(self, query: "Query") -> Any:
        """
        Handle exists query.

        Args:
            query: Exists query.

        Returns:
            Result of exists operation.
        """
        payload = query.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required for exists query")

        exists = memory_id in self._memory_store

        logger.debug(f"Memory exists check: {memory_id} -> {exists}")

        return {
            "memory_id": memory_id,
            "exists": exists,
        }

    async def _handle_count_query(self, query: "Query") -> Any:
        """
        Handle count query.

        Args:
            query: Count query.

        Returns:
            Result of count operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})

        # Count memories
        count = 0
        for memory_id, data in self._memory_store.items():
            metadata = self._memory_metadata.get(memory_id, {})

            # Apply filter
            if filter and not all(metadata.get(k) == v for k, v in filter.items()):
                continue

            count += 1

        logger.debug(f"Memory count: {count}")

        return {
            "count": count,
        }

    # Event Handlers

    async def _handle_memory_save_event(self, event: "Event") -> None:
        """
        Handle memory save event.

        Args:
            event: Memory save event.
        """
        logger.debug(f"Memory save event received: {event.payload}")
        # Could update local cache or trigger other actions

    async def _handle_memory_delete_event(self, event: "Event") -> None:
        """
        Handle memory delete event.

        Args:
            event: Memory delete event.
        """
        logger.debug(f"Memory delete event received: {event.payload}")
        # Could update local cache or trigger other actions

    # Additional Methods

    def get_memory(self, memory_id: str) -> Optional[Any]:
        """
        Get a memory by ID (synchronous).

        Args:
            memory_id: ID of the memory to get.

        Returns:
            Memory data if found, None otherwise.
        """
        return self._memory_store.get(memory_id)

    def set_memory(self, memory_id: str, data: Any, metadata: Dict[str, Any] = None) -> None:
        """
        Set a memory (synchronous).

        Args:
            memory_id: ID of the memory to set.
            data: Memory data.
            metadata: Memory metadata.
        """
        self._memory_store[memory_id] = data
        if metadata:
            self._memory_metadata[memory_id] = metadata

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory (synchronous).

        Args:
            memory_id: ID of the memory to delete.

        Returns:
            True if memory was deleted, False otherwise.
        """
        if memory_id in self._memory_store:
            del self._memory_store[memory_id]
            if memory_id in self._memory_metadata:
                del self._memory_metadata[memory_id]
            return True
        return False

    def list_memories(self) -> List[str]:
        """
        List all memory IDs (synchronous).

        Returns:
            List of memory IDs.
        """
        return list(self._memory_store.keys())

    def clear_memories(self) -> int:
        """
        Clear all memories (synchronous).

        Returns:
            Number of memories cleared.
        """
        count = len(self._memory_store)
        self._memory_store.clear()
        self._memory_metadata.clear()
        return count

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MemoryRuntimeExample("
            f"id={self.runtime_id}, "
            f"name={self.config.name}, "
            f"memories={len(self._memory_store)})"
        )
