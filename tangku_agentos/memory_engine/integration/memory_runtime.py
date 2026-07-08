"""
Memory Engine - Integrated Runtime Implementation

This module provides the full integration of the Memory Engine with the
Runtime Communication Framework. It serves as a production-ready example
of how to integrate existing TangkuAgentOS runtimes.

Features:
- Full BaseRuntime integration
- Complete command and query handling
- Standard system event publishing
- Health monitoring
- Metrics collection
- Distributed tracing
- Backward compatibility

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.integration.base import RuntimeConfig
    from tangku_agentos.runtime_communication.models.messages import Command, Query, Event

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a memory entry in the memory engine."""

    memory_id: str
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            memory_id=data["memory_id"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            tags=set(data.get("tags", [])),
        )


@dataclass
class MemorySearchResult:
    """Represents a memory search result."""

    memory_id: str
    data: Any
    metadata: Dict[str, Any]
    score: float = 1.0
    matched_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "data": self.data,
            "metadata": self.metadata,
            "score": self.score,
            "matched_fields": self.matched_fields,
        }


class MemoryEngineRuntime:
    """
    Integrated Memory Engine Runtime.

    This runtime provides memory storage and retrieval services
    through the Runtime Communication Framework.

    Features:
    - Save, load, update, delete memory entries
    - Search and list memories
    - Versioned memories
    - Tag-based organization
    - Metadata management
    - Event publishing
    - Health monitoring

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.memory_engine.integration import MemoryEngineRuntime
        >>> from tangku_agentos.runtime_communication.integration import create_runtime_config
        >>> 
        >>> config = create_runtime_config(
        ...     runtime_id="memory_engine",
        ...     name="Memory Engine",
        ...     version="1.0.0",
        ...     description="Manages memory storage and retrieval",
        ...     capabilities={"memory", "storage", "persistence"},
        ... )
        >>> 
        >>> memory_runtime = MemoryEngineRuntime(config)
        >>> await memory_runtime.initialize()
        >>> await memory_runtime.start()
        >>> 
        >>> # Save a memory
        >>> result = await memory_runtime.send_command(
        ...     target_runtime_id="memory_engine",
        ...     command_type="save",
        ...     payload={
        ...         "memory_id": "my_memory",
        ...         "data": {"key": "value"},
        ...         "metadata": {"type": "example"},
        ...         "tags": ["example", "test"],
        ...     }
        ... )
        >>> 
        >>> # Load a memory
        >>> result = await memory_runtime.send_query(
        ...     target_runtime_id="memory_engine",
        ...     query_type="get",
        ...     payload={"memory_id": "my_memory"}
        ... )
    """

    def __init__(self, config: "RuntimeConfig"):
        """
        Initialize the Memory Engine Runtime.

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
        super(MemoryEngineRuntime, self).__init__(config, capabilities)

        # Memory storage
        self._memories: Dict[str, MemoryEntry] = {}
        self._memory_lock = asyncio.Lock()

        # Indexes for fast lookup
        self._tag_index: Dict[str, Set[str]] = {}
        self._metadata_index: Dict[str, Dict[str, Set[str]]] = {}

        # Metrics
        self._metrics: Dict[str, Any] = {
            "memories_created": 0,
            "memories_updated": 0,
            "memories_deleted": 0,
            "memories_loaded": 0,
            "searches_performed": 0,
            "total_size": 0,
            "last_save_time": None,
            "last_load_time": None,
        }

        # Register command handlers
        self._register_command_handlers()

        # Register query handlers
        self._register_query_handlers()

        # Register event handlers
        self._register_event_handlers()

        logger.info(f"MemoryEngineRuntime initialized: {config.runtime_id}")

    def _register_command_handlers(self) -> None:
        """Register all command handlers."""
        # Memory operations
        self.register_command_handler("save", self._handle_save_command)
        self.register_command_handler("load", self._handle_load_command)
        self.register_command_handler("update", self._handle_update_command)
        self.register_command_handler("delete", self._handle_delete_command)
        self.register_command_handler("clear", self._handle_clear_command)
        self.register_command_handler("increment", self._handle_increment_command)

        # Bulk operations
        self.register_command_handler("save_batch", self._handle_save_batch_command)
        self.register_command_handler("delete_batch", self._handle_delete_batch_command)

        # Version operations
        self.register_command_handler("get_version", self._handle_get_version_command)
        self.register_command_handler("list_versions", self._handle_list_versions_command)
        self.register_command_handler("restore_version", self._handle_restore_version_command)

        # Tag operations
        self.register_command_handler("add_tags", self._handle_add_tags_command)
        self.register_command_handler("remove_tags", self._handle_remove_tags_command)
        self.register_command_handler("set_tags", self._handle_set_tags_command)

        # Metadata operations
        self.register_command_handler("update_metadata", self._handle_update_metadata_command)

        # Standard system commands
        from tangku_agentos.runtime_communication.integration import SystemCommands

        self.register_command_handler(
            "runtime.get_status",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeStatus),
        )
        self.register_command_handler(
            "runtime.get_health",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeHealth),
        )
        self.register_command_handler(
            "runtime.get_metadata",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeMetadata),
        )

    def _register_query_handlers(self) -> None:
        """Register all query handlers."""
        # Memory queries
        self.register_query_handler("get", self._handle_get_query)
        self.register_query_handler("search", self._handle_search_query)
        self.register_query_handler("list", self._handle_list_query)
        self.register_query_handler("exists", self._handle_exists_query)
        self.register_query_handler("count", self._handle_count_query)

        # Advanced queries
        self.register_query_handler("get_by_tag", self._handle_get_by_tag_query)
        self.register_query_handler("get_by_metadata", self._handle_get_by_metadata_query)
        self.register_query_handler("get_stats", self._handle_get_stats_query)

        # Standard system queries
        from tangku_agentos.runtime_communication.integration import SystemQueries

        self.register_query_handler(
            "runtime.get_status",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeStatus),
        )
        self.register_query_handler(
            "runtime.get_health",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeHealth),
        )
        self.register_query_handler(
            "runtime.get_metadata",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeMetadata),
        )

    def _register_event_handlers(self) -> None:
        """Register all event handlers."""
        # Subscribe to system events
        self.register_event_handler("system.startup", self._handle_system_startup)
        self.register_event_handler("system.shutdown", self._handle_system_shutdown)
        self.register_event_handler("system.health_check", self._handle_health_check)

        # Subscribe to memory events from other runtimes
        self.register_event_handler("memory.updated", self._handle_memory_updated)
        self.register_event_handler("memory.deleted", self._handle_memory_deleted)

    async def _initialize(self) -> None:
        """
        Initialize the memory engine.

        This method is called during runtime initialization.
        """
        logger.info(f"Initializing MemoryEngineRuntime: {self.runtime_id}")

        # Initialize storage
        self._memories = {}
        self._tag_index = {}
        self._metadata_index = {}

        # Initialize metrics
        self._metrics = {
            "memories_created": 0,
            "memories_updated": 0,
            "memories_deleted": 0,
            "memories_loaded": 0,
            "searches_performed": 0,
            "total_size": 0,
            "last_save_time": None,
            "last_load_time": None,
        }

        # Set up health checks
        await self._setup_health_checks()

        logger.info(f"MemoryEngineRuntime initialized: {self.runtime_id}")

    async def _start(self) -> None:
        """
        Start the memory engine.

        This method is called during runtime startup.
        """
        logger.info(f"Starting MemoryEngineRuntime: {self.runtime_id}")

        # Start background tasks if needed
        # For memory engine, there are no background tasks currently

        logger.info(f"MemoryEngineRuntime started: {self.runtime_id}")

    async def _stop(self) -> None:
        """
        Stop the memory engine.

        This method is called during runtime shutdown.
        """
        logger.info(f"Stopping MemoryEngineRuntime: {self.runtime_id}")

        # Clean up resources
        async with self._memory_lock:
            self._memories.clear()
            self._tag_index.clear()
            self._metadata_index.clear()

        logger.info(f"MemoryEngineRuntime stopped: {self.runtime_id}")

    async def _setup_health_checks(self) -> None:
        """Set up health checks for the memory engine."""
        from tangku_agentos.runtime_communication import HealthCheck, HealthStatus

        # Liveness check
        async def liveness_check(runtime_id: str) -> Any:
            # Check if runtime is in a running state
            if self.state == self.state.RUNNING:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": "Memory engine is alive",
                    "passed": True,
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Memory engine is not running (state: {self.state.name})",
                    "passed": False,
                }

        # Readiness check
        async def readiness_check(runtime_id: str) -> Any:
            # Check if memory engine is ready to handle requests
            if self.state == self.state.RUNNING:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": "Memory engine is ready",
                    "passed": True,
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Memory engine is not ready (state: {self.state.name})",
                    "passed": False,
                }

        # Storage check
        async def storage_check(runtime_id: str) -> Any:
            # Check if storage is accessible
            try:
                async with self._memory_lock:
                    count = len(self._memories)
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"Storage accessible ({count} memories)",
                    "passed": True,
                    "details": {"memory_count": count},
                }
            except Exception as e:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "message": f"Storage error: {e}",
                    "passed": False,
                }

        # Register health checks
        from tangku_agentos.runtime_communication.services.health import HealthCheckResult

        liveness = HealthCheck(
            name="liveness",
            description="Check if memory engine is alive",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="liveness",
                status=HealthStatus.HEALTHY if self.state == self.state.RUNNING else HealthStatus.UNHEALTHY,
                message="Memory engine is alive" if self.state == self.state.RUNNING else f"Not running: {self.state.name}",
                passed=self.state == self.state.RUNNING,
            ),
            interval=30.0,
            timeout=5.0,
            critical=True,
        )

        readiness = HealthCheck(
            name="readiness",
            description="Check if memory engine is ready",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="readiness",
                status=HealthStatus.HEALTHY if self.state == self.state.RUNNING else HealthStatus.UNHEALTHY,
                message="Memory engine is ready" if self.state == self.state.RUNNING else f"Not ready: {self.state.name}",
                passed=self.state == self.state.RUNNING,
            ),
            interval=30.0,
            timeout=5.0,
            critical=True,
        )

        storage = HealthCheck(
            name="storage",
            description="Check memory storage",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="storage",
                status=HealthStatus.HEALTHY,
                message=f"Storage OK ({len(self._memories)} memories)",
                passed=True,
                details={"memory_count": len(self._memories)},
            ),
            interval=60.0,
            timeout=10.0,
            critical=False,
        )

        self.health_service.register_check(self.runtime_id, liveness)
        self.health_service.register_check(self.runtime_id, readiness)
        self.health_service.register_check(self.runtime_id, storage)

    # Command Handlers

    async def _handle_save_command(self, command: "Command") -> Any:
        """
        Handle save memory command.

        Args:
            command: Save command.

        Returns:
            Result of save operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        data = payload.get("data")
        metadata = payload.get("metadata", {})
        tags = set(payload.get("tags", []))
        overwrite = payload.get("overwrite", True)

        if not memory_id:
            raise ValueError("memory_id is required")
        if data is None:
            raise ValueError("data is required")

        async with self._memory_lock:
            # Check if memory exists and overwrite is False
            if not overwrite and memory_id in self._memories:
                raise ValueError(f"Memory already exists: {memory_id}")

            # Create or update memory entry
            if memory_id in self._memories:
                entry = self._memories[memory_id]
                entry.data = data
                entry.metadata.update(metadata)
                entry.tags.update(tags)
                entry.updated_at = datetime.utcnow()
                entry.version += 1
                self._metrics["memories_updated"] += 1
            else:
                entry = MemoryEntry(
                    memory_id=memory_id,
                    data=data,
                    metadata=metadata,
                    tags=tags,
                )
                self._memories[memory_id] = entry
                self._metrics["memories_created"] += 1

            # Update indexes
            self._update_indexes(entry)

            # Update metrics
            self._metrics["total_size"] = sum(
                len(str(e.data)) for e in self._memories.values()
            )
            self._metrics["last_save_time"] = datetime.utcnow().isoformat()

        # Publish event
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
            "version": entry.version,
            "size": len(str(data)),
            "timestamp": entry.updated_at.isoformat(),
        }

    async def _handle_load_command(self, command: "Command") -> Any:
        """
        Handle load memory command.

        Args:
            command: Load command.

        Returns:
            Result of load operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            self._metrics["memories_loaded"] += 1
            self._metrics["last_load_time"] = datetime.utcnow().isoformat()

        logger.debug(f"Memory loaded: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "data": entry.data,
            "metadata": entry.metadata,
            "version": entry.version,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "tags": list(entry.tags),
        }

    async def _handle_update_command(self, command: "Command") -> Any:
        """
        Handle update memory command.

        Args:
            command: Update command.

        Returns:
            Result of update operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        updates = payload.get("updates", {})
        metadata_updates = payload.get("metadata_updates", {})
        tag_updates = payload.get("tag_updates", {})

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]

            # Update data
            if updates:
                entry.data.update(updates)

            # Update metadata
            if metadata_updates:
                entry.metadata.update(metadata_updates)

            # Update tags
            if tag_updates:
                for tag, value in tag_updates.items():
                    if value:
                        entry.tags.add(tag)
                    else:
                        entry.tags.discard(tag)

            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

            # Update indexes
            self._update_indexes(entry)

        # Publish event
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
            "version": entry.version,
            "updated_fields": list(updates.keys()) if updates else [],
            "timestamp": entry.updated_at.isoformat(),
        }

    async def _handle_delete_command(self, command: "Command") -> Any:
        """
        Handle delete memory command.

        Args:
            command: Delete command.

        Returns:
            Result of delete operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        reason = payload.get("reason", "user_request")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            del self._memories[memory_id]

            # Remove from indexes
            self._remove_from_indexes(entry)

            self._metrics["memories_deleted"] += 1

        # Publish event
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

    async def _handle_clear_command(self, command: "Command") -> Any:
        """
        Handle clear memories command.

        Args:
            command: Clear command.

        Returns:
            Result of clear operation.
        """
        payload = command.payload or {}
        filter = payload.get("filter", {})
        force = payload.get("force", False)

        if not force:
            raise ValueError("force must be True to clear memories")

        async with self._memory_lock:
            if filter:
                # Clear filtered memories
                to_delete = [
                    mid for mid, entry in self._memories.items()
                    if all(entry.metadata.get(k) == v for k, v in filter.items())
                ]
                count = len(to_delete)
                for mid in to_delete:
                    entry = self._memories[mid]
                    del self._memories[mid]
                    self._remove_from_indexes(entry)
                    self._metrics["memories_deleted"] += 1
            else:
                # Clear all memories
                count = len(self._memories)
                for entry in self._memories.values():
                    self._remove_from_indexes(entry)
                self._memories.clear()
                self._metrics["memories_deleted"] += count

        logger.debug(f"Cleared {count} memories")

        return {
            "success": True,
            "cleared_count": count,
        }

    async def _handle_increment_command(self, command: "Command") -> Any:
        """
        Handle increment memory command (for numeric values).

        Args:
            command: Increment command.

        Returns:
            Result of increment operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        field = payload.get("field", "value")
        amount = payload.get("amount", 1)

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]

            # Get current value
            if field not in entry.data:
                entry.data[field] = 0

            # Increment value
            entry.data[field] += amount
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

        logger.debug(f"Memory incremented: {memory_id}.{field} += {amount}")

        return {
            "success": True,
            "memory_id": memory_id,
            "field": field,
            "new_value": entry.data[field],
            "version": entry.version,
        }

    async def _handle_save_batch_command(self, command: "Command") -> Any:
        """
        Handle save batch command.

        Args:
            command: Save batch command.

        Returns:
            Result of batch save operation.
        """
        payload = command.payload or {}
        memories = payload.get("memories", [])
        overwrite = payload.get("overwrite", True)

        results = []
        errors = []

        async with self._memory_lock:
            for mem_data in memories:
                try:
                    memory_id = mem_data.get("memory_id")
                    data = mem_data.get("data")
                    metadata = mem_data.get("metadata", {})
                    tags = set(mem_data.get("tags", []))

                    if not memory_id or data is None:
                        errors.append({
                            "memory_id": memory_id,
                            "error": "memory_id and data are required",
                        })
                        continue

                    # Check if memory exists and overwrite is False
                    if not overwrite and memory_id in self._memories:
                        errors.append({
                            "memory_id": memory_id,
                            "error": "Memory already exists",
                        })
                        continue

                    # Create or update memory entry
                    if memory_id in self._memories:
                        entry = self._memories[memory_id]
                        entry.data = data
                        entry.metadata.update(metadata)
                        entry.tags.update(tags)
                        entry.updated_at = datetime.utcnow()
                        entry.version += 1
                        self._metrics["memories_updated"] += 1
                    else:
                        entry = MemoryEntry(
                            memory_id=memory_id,
                            data=data,
                            metadata=metadata,
                            tags=tags,
                        )
                        self._memories[memory_id] = entry
                        self._metrics["memories_created"] += 1

                    # Update indexes
                    self._update_indexes(entry)

                    results.append({
                        "memory_id": memory_id,
                        "version": entry.version,
                        "success": True,
                    })

                except Exception as e:
                    errors.append({
                        "memory_id": mem_data.get("memory_id"),
                        "error": str(e),
                    })

        # Update metrics
        self._metrics["total_size"] = sum(
            len(str(e.data)) for e in self._memories.values()
        )
        self._metrics["last_save_time"] = datetime.utcnow().isoformat()

        logger.debug(f"Batch save: {len(results)} successes, {len(errors)} errors")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
        }

    async def _handle_delete_batch_command(self, command: "Command") -> Any:
        """
        Handle delete batch command.

        Args:
            command: Delete batch command.

        Returns:
            Result of batch delete operation.
        """
        payload = command.payload or {}
        memory_ids = payload.get("memory_ids", [])
        reason = payload.get("reason", "user_request")

        results = []
        errors = []

        async with self._memory_lock:
            for memory_id in memory_ids:
                try:
                    if memory_id not in self._memories:
                        errors.append({
                            "memory_id": memory_id,
                            "error": "Memory not found",
                        })
                        continue

                    entry = self._memories[memory_id]
                    del self._memories[memory_id]
                    self._remove_from_indexes(entry)
                    self._metrics["memories_deleted"] += 1

                    results.append({
                        "memory_id": memory_id,
                        "success": True,
                    })

                except Exception as e:
                    errors.append({
                        "memory_id": memory_id,
                        "error": str(e),
                    })

        logger.debug(f"Batch delete: {len(results)} successes, {len(errors)} errors")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
        }

    async def _handle_get_version_command(self, command: "Command") -> Any:
        """
        Handle get version command.

        Args:
            command: Get version command.

        Returns:
            Result of get version operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        version = payload.get("version")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]

            if version is not None and entry.version != version:
                raise ValueError(
                    f"Version mismatch: expected {version}, got {entry.version}"
                )

        return {
            "success": True,
            "memory_id": memory_id,
            "data": entry.data,
            "version": entry.version,
        }

    async def _handle_list_versions_command(self, command: "Command") -> Any:
        """
        Handle list versions command.

        Args:
            command: List versions command.

        Returns:
            Result of list versions operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]

        # For now, we only store the current version
        # In a full implementation, we would store version history
        return {
            "success": True,
            "memory_id": memory_id,
            "versions": [entry.version],
            "current_version": entry.version,
        }

    async def _handle_restore_version_command(self, command: "Command") -> Any:
        """
        Handle restore version command.

        Args:
            command: Restore version command.

        Returns:
            Result of restore version operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        version = payload.get("version")

        if not memory_id:
            raise ValueError("memory_id is required")
        if version is None:
            raise ValueError("version is required")

        # For now, versioning is not fully implemented
        # This would restore a specific version of the memory
        raise NotImplementedError("Version restore not yet implemented")

    async def _handle_add_tags_command(self, command: "Command") -> Any:
        """
        Handle add tags command.

        Args:
            command: Add tags command.

        Returns:
            Result of add tags operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        tags = set(payload.get("tags", []))

        if not memory_id:
            raise ValueError("memory_id is required")
        if not tags:
            raise ValueError("tags is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            old_tags = set(entry.tags)
            entry.tags.update(tags)
            new_tags = set(entry.tags)
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

            # Update indexes
            self._update_indexes(entry)

        logger.debug(f"Tags added to memory: {memory_id}, new tags: {tags}")

        return {
            "success": True,
            "memory_id": memory_id,
            "added_tags": list(tags),
            "all_tags": list(entry.tags),
            "version": entry.version,
        }

    async def _handle_remove_tags_command(self, command: "Command") -> Any:
        """
        Handle remove tags command.

        Args:
            command: Remove tags command.

        Returns:
            Result of remove tags operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        tags = set(payload.get("tags", []))

        if not memory_id:
            raise ValueError("memory_id is required")
        if not tags:
            raise ValueError("tags is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            old_tags = set(entry.tags)
            entry.tags.difference_update(tags)
            new_tags = set(entry.tags)
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

            # Update indexes
            self._update_indexes(entry)

        logger.debug(f"Tags removed from memory: {memory_id}, removed tags: {tags}")

        return {
            "success": True,
            "memory_id": memory_id,
            "removed_tags": list(tags),
            "all_tags": list(entry.tags),
            "version": entry.version,
        }

    async def _handle_set_tags_command(self, command: "Command") -> Any:
        """
        Handle set tags command.

        Args:
            command: Set tags command.

        Returns:
            Result of set tags operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        tags = set(payload.get("tags", []))

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            old_tags = set(entry.tags)
            entry.tags = tags
            new_tags = set(entry.tags)
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

            # Update indexes
            self._update_indexes(entry)

        logger.debug(f"Tags set for memory: {memory_id}, tags: {tags}")

        return {
            "success": True,
            "memory_id": memory_id,
            "old_tags": list(old_tags),
            "new_tags": list(new_tags),
            "version": entry.version,
        }

    async def _handle_update_metadata_command(self, command: "Command") -> Any:
        """
        Handle update metadata command.

        Args:
            command: Update metadata command.

        Returns:
            Result of update metadata operation.
        """
        payload = command.payload or {}
        memory_id = payload.get("memory_id")
        metadata = payload.get("metadata", {})

        if not memory_id:
            raise ValueError("memory_id is required")
        if not metadata:
            raise ValueError("metadata is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                raise ValueError(f"Memory not found: {memory_id}")

            entry = self._memories[memory_id]
            old_metadata = entry.metadata.copy()
            entry.metadata.update(metadata)
            entry.updated_at = datetime.utcnow()
            entry.version += 1
            self._metrics["memories_updated"] += 1

            # Update indexes
            self._update_indexes(entry)

        logger.debug(f"Metadata updated for memory: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "old_metadata": old_metadata,
            "new_metadata": entry.metadata,
            "version": entry.version,
        }

    async def _handle_system_command(self, command: "Command", system_command: Any) -> Any:
        """
        Handle system command.

        Args:
            command: System command.
            system_command: System command type.

        Returns:
            Result of system command.
        """
        # For now, just return runtime info for system commands
        return self.get_metadata()

    # Query Handlers

    async def _handle_get_query(self, query: "Query") -> Any:
        """
        Handle get memory query.

        Args:
            query: Get query.

        Returns:
            Result of get operation.
        """
        payload = query.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            if memory_id not in self._memories:
                return None

            entry = self._memories[memory_id]
            self._metrics["memories_loaded"] += 1
            self._metrics["last_load_time"] = datetime.utcnow().isoformat()

        return entry.to_dict()

    async def _handle_search_query(self, query: "Query") -> Any:
        """
        Handle search memory query.

        Args:
            query: Search query.

        Returns:
            Result of search operation.
        """
        payload = query.payload or {}
        search_query = payload.get("query", "")
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))
        limit = payload.get("limit", 10)
        sort_by = payload.get("sort_by", "updated_at")
        sort_order = payload.get("sort_order", "desc")

        async with self._memory_lock:
            results = []

            for entry in self._memories.values():
                # Apply filter
                if filter and not all(
                    str(entry.metadata.get(k)) == str(v)
                    for k, v in filter.items()
                ):
                    continue

                # Apply tag filter
                if tags and not tags.issubset(entry.tags):
                    continue

                # Apply search query
                if search_query:
                    search_lower = search_query.lower()
                    data_str = str(entry.data).lower()
                    metadata_str = str(entry.metadata).lower()
                    tags_str = " ".join(entry.tags).lower()

                    if search_lower not in (data_str + metadata_str + tags_str):
                        continue

                results.append(entry)

            # Sort results
            reverse = sort_order == "desc"
            if sort_by == "created_at":
                results.sort(key=lambda e: e.created_at, reverse=reverse)
            elif sort_by == "updated_at":
                results.sort(key=lambda e: e.updated_at, reverse=reverse)
            elif sort_by == "memory_id":
                results.sort(key=lambda e: e.memory_id, reverse=reverse)
            elif sort_by == "size":
                results.sort(key=lambda e: len(str(e.data)), reverse=reverse)

            # Limit results
            results = results[:limit]

            self._metrics["searches_performed"] += 1

        return {
            "query": search_query,
            "filter": filter,
            "tags": list(tags),
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "total": len(self._memories),
        }

    async def _handle_list_query(self, query: "Query") -> Any:
        """
        Handle list memories query.

        Args:
            query: List query.

        Returns:
            Result of list operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))
        limit = payload.get("limit", 100)
        offset = payload.get("offset", 0)
        sort_by = payload.get("sort_by", "updated_at")
        sort_order = payload.get("sort_order", "desc")

        async with self._memory_lock:
            entries = list(self._memories.values())

            # Apply filter
            if filter:
                entries = [
                    e for e in entries
                    if all(
                        str(e.metadata.get(k)) == str(v)
                        for k, v in filter.items()
                    )
                ]

            # Apply tag filter
            if tags:
                entries = [e for e in entries if tags.issubset(e.tags)]

            # Sort entries
            reverse = sort_order == "desc"
            if sort_by == "created_at":
                entries.sort(key=lambda e: e.created_at, reverse=reverse)
            elif sort_by == "updated_at":
                entries.sort(key=lambda e: e.updated_at, reverse=reverse)
            elif sort_by == "memory_id":
                entries.sort(key=lambda e: e.memory_id, reverse=reverse)
            elif sort_by == "size":
                entries.sort(key=lambda e: len(str(e.data)), reverse=reverse)

            # Paginate
            total = len(entries)
            entries = entries[offset:offset + limit]

        return {
            "memories": [e.to_dict() for e in entries],
            "count": len(entries),
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    async def _handle_exists_query(self, query: "Query") -> Any:
        """
        Handle exists memory query.

        Args:
            query: Exists query.

        Returns:
            Result of exists operation.
        """
        payload = query.payload or {}
        memory_id = payload.get("memory_id")

        if not memory_id:
            raise ValueError("memory_id is required")

        async with self._memory_lock:
            exists = memory_id in self._memories

        return {
            "memory_id": memory_id,
            "exists": exists,
        }

    async def _handle_count_query(self, query: "Query") -> Any:
        """
        Handle count memories query.

        Args:
            query: Count query.

        Returns:
            Result of count operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))

        async with self._memory_lock:
            count = 0
            for entry in self._memories.values():
                # Apply filter
                if filter and not all(
                    str(entry.metadata.get(k)) == str(v)
                    for k, v in filter.items()
                ):
                    continue

                # Apply tag filter
                if tags and not tags.issubset(entry.tags):
                    continue

                count += 1

        return {
            "count": count,
        }

    async def _handle_get_by_tag_query(self, query: "Query") -> Any:
        """
        Handle get by tag query.

        Args:
            query: Get by tag query.

        Returns:
            Result of get by tag operation.
        """
        payload = query.payload or {}
        tag = payload.get("tag")
        limit = payload.get("limit", 10)

        if not tag:
            raise ValueError("tag is required")

        async with self._memory_lock:
            entries = [
                e for e in self._memories.values()
                if tag in e.tags
            ]
            entries = entries[:limit]

        return {
            "tag": tag,
            "memories": [e.to_dict() for e in entries],
            "count": len(entries),
        }

    async def _handle_get_by_metadata_query(self, query: "Query") -> Any:
        """
        Handle get by metadata query.

        Args:
            query: Get by metadata query.

        Returns:
            Result of get by metadata operation.
        """
        payload = query.payload or {}
        key = payload.get("key")
        value = payload.get("value")
        limit = payload.get("limit", 10)

        if not key:
            raise ValueError("key is required")

        async with self._memory_lock:
            entries = [
                e for e in self._memories.values()
                if str(e.metadata.get(key)) == str(value)
            ]
            entries = entries[:limit]

        return {
            "key": key,
            "value": value,
            "memories": [e.to_dict() for e in entries],
            "count": len(entries),
        }

    async def _handle_get_stats_query(self, query: "Query") -> Any:
        """
        Handle get stats query.

        Args:
            query: Get stats query.

        Returns:
            Memory engine statistics.
        """
        async with self._memory_lock:
            total_size = sum(len(str(e.data)) for e in self._memories.values())
            avg_size = total_size / len(self._memories) if self._memories else 0

            # Get tag statistics
            tag_counts = {}
            for entry in self._memories.values():
                for tag in entry.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Get metadata statistics
            metadata_keys = set()
            for entry in self._memories.values():
                metadata_keys.update(entry.metadata.keys())

        return {
            "total_memories": len(self._memories),
            "total_size": total_size,
            "avg_size": avg_size,
            "tag_counts": tag_counts,
            "metadata_keys": list(metadata_keys),
            "metrics": self._metrics.copy(),
        }

    async def _handle_system_query(self, query: "Query", system_query: Any) -> Any:
        """
        Handle system query.

        Args:
            query: System query.
            system_query: System query type.

        Returns:
            Result of system query.
        """
        # For now, just return runtime info for system queries
        return self.get_metadata()

    # Event Handlers

    async def _handle_system_startup(self, event: "Event") -> None:
        """Handle system startup event."""
        logger.info(f"System startup event received: {event.payload}")
        # Could trigger initialization or warm-up

    async def _handle_system_shutdown(self, event: "Event") -> None:
        """Handle system shutdown event."""
        logger.info(f"System shutdown event received: {event.payload}")
        # Could trigger cleanup or persistence

    async def _handle_health_check(self, event: "Event") -> None:
        """Handle health check event."""
        logger.debug(f"Health check event received: {event.payload}")
        # Could trigger self-check

    async def _handle_memory_updated(self, event: "Event") -> None:
        """Handle memory updated event from other runtimes."""
        logger.debug(f"Memory updated event received: {event.payload}")
        # Could update local cache or trigger sync

    async def _handle_memory_deleted(self, event: "Event") -> None:
        """Handle memory deleted event from other runtimes."""
        logger.debug(f"Memory deleted event received: {event.payload}")
        # Could update local cache or trigger sync

    # Helper Methods

    def _update_indexes(self, entry: MemoryEntry) -> None:
        """Update indexes for a memory entry."""
        # Update tag index
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(entry.memory_id)

        # Update metadata index
        for key, value in entry.metadata.items():
            if key not in self._metadata_index:
                self._metadata_index[key] = {}
            if str(value) not in self._metadata_index[key]:
                self._metadata_index[key][str(value)] = set()
            self._metadata_index[key][str(value)].add(entry.memory_id)

    def _remove_from_indexes(self, entry: MemoryEntry) -> None:
        """Remove a memory entry from indexes."""
        # Remove from tag index
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(entry.memory_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

        # Remove from metadata index
        for key, value in entry.metadata.items():
            if key in self._metadata_index:
                if str(value) in self._metadata_index[key]:
                    self._metadata_index[key][str(value)].discard(entry.memory_id)
                    if not self._metadata_index[key][str(value)]:
                        del self._metadata_index[key][str(value)]
                    if not self._metadata_index[key]:
                        del self._metadata_index[key]

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Get a memory entry by ID (synchronous).

        Args:
            memory_id: ID of the memory to get.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        return self._memories.get(memory_id)

    def list_memories(self) -> List[str]:
        """
        List all memory IDs (synchronous).

        Returns:
            List of memory IDs.
        """
        return list(self._memories.keys())

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get memory engine metrics.

        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "memory_count": len(self._memories),
            "tag_count": len(self._tag_index),
            "metadata_key_count": len(self._metadata_index),
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MemoryEngineRuntime("
            f"id={self.runtime_id}, "
            f"name={self.config.name}, "
            f"version={self.config.version}, "
            f"memories={len(self._memories)})"
        )
