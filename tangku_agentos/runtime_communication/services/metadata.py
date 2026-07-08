"""
Runtime Communication Framework - Runtime Metadata Registry

The RuntimeMetadataRegistry provides metadata management for TangkuAgentOS
runtimes. It enables:
- Runtime metadata storage and retrieval
- Metadata validation
- Metadata versioning
- Metadata search and filtering
- Metadata change notifications

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.services.registry import (
        RuntimeRegistry,
        RuntimeInfo,
    )

logger = logging.getLogger(__name__)


@dataclass
class MetadataChange:
    """
    Represents a change in runtime metadata.

    Attributes:
        runtime_id: ID of the runtime.
        key: Metadata key that changed.
        old_value: Previous value.
        new_value: New value.
        timestamp: When the change occurred.
        changed_by: Who made the change.
        reason: Reason for the change.
    """

    runtime_id: str
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    changed_by: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "changed_by": self.changed_by,
            "reason": self.reason,
        }


@dataclass
class MetadataSchema:
    """
    Schema definition for runtime metadata.

    Attributes:
        name: Name of the schema.
        description: Description of the schema.
        required_keys: Set of required metadata keys.
        optional_keys: Set of optional metadata keys.
        key_types: Dictionary mapping keys to expected types.
        validators: Dictionary mapping keys to validation functions.
        default_values: Dictionary of default values for keys.
    """

    name: str
    description: str = ""
    required_keys: Set[str] = field(default_factory=set)
    optional_keys: Set[str] = field(default_factory=set)
    key_types: Dict[str, type] = field(default_factory=dict)
    validators: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    default_values: Dict[str, Any] = field(default_factory=dict)

    def validate(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate metadata against the schema.

        Args:
            metadata: Metadata to validate.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Check required keys
        for key in self.required_keys:
            if key not in metadata:
                errors.append(f"Missing required key: {key}")

        # Check types
        for key, expected_type in self.key_types.items():
            if key in metadata:
                value = metadata[key]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Wrong type for key '{key}': expected {expected_type}, "
                        f"got {type(value)}"
                    )

        # Check validators
        for key, validator in self.validators.items():
            if key in metadata:
                value = metadata[key]
                try:
                    if not validator(value):
                        errors.append(f"Validation failed for key '{key}'")
                except Exception as e:
                    errors.append(f"Validator error for key '{key}': {e}")

        return errors


@dataclass
class MetadataVersion:
    """
    Version information for runtime metadata.

    Attributes:
        runtime_id: ID of the runtime.
        version: Version number.
        metadata: Metadata at this version.
        timestamp: When this version was created.
        changed_by: Who made the changes.
        changes: List of changes from previous version.
    """

    runtime_id: str
    version: int
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    changed_by: str = ""
    changes: List[MetadataChange] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "version": self.version,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "changed_by": self.changed_by,
            "changes": [c.to_dict() for c in self.changes],
        }


class RuntimeMetadataRegistry:
    """
    Metadata registry for TangkuAgentOS runtimes.

    The RuntimeMetadataRegistry provides centralized metadata management
    for runtimes. It enables storage, retrieval, validation, and versioning
    of runtime metadata.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.metadata import RuntimeMetadataRegistry
        >>> from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
        >>> 
        >>> registry = RuntimeRegistry()
        >>> metadata_registry = RuntimeMetadataRegistry(registry)
        >>> 
        >>> # Register a runtime
        >>> registry.register("memory_runtime", name="Memory Runtime")
        >>> 
        >>> # Set metadata
        >>> metadata_registry.set("memory_runtime", "version", "1.0.0")
        >>> metadata_registry.set("memory_runtime", "config", {"max_size": 1024})
        >>> 
        >>> # Get metadata
        >>> version = metadata_registry.get("memory_runtime", "version")
        >>> config = metadata_registry.get("memory_runtime", "config")

    Attributes:
        registry: Runtime registry to use.
        max_versions: Maximum number of metadata versions to keep per runtime.
    """

    def __init__(
        self,
        registry: Optional["RuntimeRegistry"] = None,
        max_versions: int = 100,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime metadata registry.

        Args:
            registry: Runtime registry to use.
            max_versions: Maximum number of metadata versions to keep per runtime.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        self._registry = registry
        self._owns_registry = registry is None

        if self._registry is None:
            from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry

            self._registry = RuntimeRegistry()

        # Metadata storage: runtime_id -> Dict[str, Any]
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._metadata_lock = asyncio.Lock()

        # Metadata versions: runtime_id -> List[MetadataVersion]
        self._versions: Dict[str, List[MetadataVersion]] = {}
        self._versions_lock = asyncio.Lock()
        self._max_versions = max_versions

        # Metadata schemas: schema_name -> MetadataSchema
        self._schemas: Dict[str, MetadataSchema] = {}
        self._schemas_lock = asyncio.Lock()

        # Metadata change callbacks
        self._on_change: List[Callable[[str, str, Any, Any], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "metadata_set": 0,
            "metadata_get": 0,
            "metadata_updated": 0,
            "metadata_deleted": 0,
            "metadata_versions": 0,
            "validation_errors": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"RuntimeMetadataRegistry initialized with max_versions={max_versions}"
        )

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        return self._registry

    def set(
        self,
        runtime_id: str,
        key: str,
        value: Any,
        changed_by: str = "",
        reason: str = "",
        validate: bool = True,
    ) -> bool:
        """
        Set metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.
            key: Metadata key.
            value: Metadata value.
            changed_by: Who made the change.
            reason: Reason for the change.
            validate: Whether to validate against schema.

        Returns:
            True if metadata was set, False otherwise.

        Raises:
            RuntimeNotFoundError: If runtime is not registered.
            MessageValidationError: If validation fails.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metadata_registry.set("memory_runtime", "version", "1.0.0")
            True
        """
        return asyncio.run(
            self._set_async(
                runtime_id, key, value, changed_by, reason, validate
            )
        )

    async def _set_async(
        self,
        runtime_id: str,
        key: str,
        value: Any,
        changed_by: str = "",
        reason: str = "",
        validate: bool = True,
    ) -> bool:
        """Async version of set."""
        # Check if runtime exists
        if self._registry.get(runtime_id) is None:
            from tangku_agentos.runtime_communication.models.exceptions import (
                RuntimeNotFoundError,
            )

            raise RuntimeNotFoundError(
                f"Runtime not found: {runtime_id}",
                runtime_id=runtime_id,
                operation="metadata_set",
            )

        # Validate against schema if requested
        if validate:
            errors = await self._validate_metadata(runtime_id, {key: value})
            if errors:
                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageValidationError,
                )

                raise MessageValidationError(
                    f"Metadata validation failed: {', '.join(errors)}",
                    validation_errors=errors,
                )

        async with self._metadata_lock:
            # Initialize metadata for runtime if not exists
            if runtime_id not in self._metadata:
                self._metadata[runtime_id] = {}

            # Get old value
            old_value = self._metadata[runtime_id].get(key)

            # Set new value
            self._metadata[runtime_id][key] = value

            # Update metrics
            async with self._metrics_lock:
                if old_value is None:
                    self._metrics["metadata_set"] += 1
                else:
                    self._metrics["metadata_updated"] += 1

            # Record version
            change = MetadataChange(
                runtime_id=runtime_id,
                key=key,
                old_value=old_value,
                new_value=value,
                changed_by=changed_by,
                reason=reason,
            )

            async with self._versions_lock:
                if runtime_id not in self._versions:
                    self._versions[runtime_id] = []

                # Get current version
                current_version = len(self._versions[runtime_id])

                # Create new version
                version = MetadataVersion(
                    runtime_id=runtime_id,
                    version=current_version + 1,
                    metadata=self._metadata[runtime_id].copy(),
                    changed_by=changed_by,
                    changes=[change],
                )

                self._versions[runtime_id].append(version)

                # Trim old versions if at capacity
                if len(self._versions[runtime_id]) > self._max_versions:
                    self._versions[runtime_id] = self._versions[runtime_id][
                        -self._max_versions :
                    ]

                async with self._metrics_lock:
                    self._metrics["metadata_versions"] += 1

            # Call change callbacks
            for callback in self._on_change:
                try:
                    callback(runtime_id, key, old_value, value)
                except Exception as e:
                    logger.error(f"Error in metadata change callback: {e}")

            if self._enable_logging:
                logger.info(
                    f"Metadata set: {runtime_id}.{key} = {value} "
                    f"(by: {changed_by}, reason: {reason})"
                )

            return True

    def get(
        self,
        runtime_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.
            key: Metadata key.
            default: Default value if key not found.

        Returns:
            Metadata value or default if not found.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> version = metadata_registry.get("memory_runtime", "version", "unknown")
        """
        async with self._metadata_lock:
            async with self._metrics_lock:
                self._metrics["metadata_get"] += 1

            if runtime_id not in self._metadata:
                return default

            return self._metadata[runtime_id].get(key, default)

    def get_all(self, runtime_id: str) -> Dict[str, Any]:
        """
        Get all metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Dictionary of all metadata for the runtime.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metadata = metadata_registry.get_all("memory_runtime")
        """
        async with self._metadata_lock:
            return self._metadata.get(runtime_id, {}).copy()

    def delete(
        self,
        runtime_id: str,
        key: str,
        changed_by: str = "",
        reason: str = "",
    ) -> bool:
        """
        Delete metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.
            key: Metadata key to delete.
            changed_by: Who made the change.
            reason: Reason for the change.

        Returns:
            True if metadata was deleted, False otherwise.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metadata_registry.delete("memory_runtime", "version")
            True
        """
        return asyncio.run(
            self._delete_async(runtime_id, key, changed_by, reason)
        )

    async def _delete_async(
        self,
        runtime_id: str,
        key: str,
        changed_by: str = "",
        reason: str = "",
    ) -> bool:
        """Async version of delete."""
        async with self._metadata_lock:
            if runtime_id not in self._metadata:
                return False

            if key not in self._metadata[runtime_id]:
                return False

            # Get old value
            old_value = self._metadata[runtime_id][key]

            # Delete key
            del self._metadata[runtime_id][key]

            # Update metrics
            async with self._metrics_lock:
                self._metrics["metadata_deleted"] += 1

            # Record version
            change = MetadataChange(
                runtime_id=runtime_id,
                key=key,
                old_value=old_value,
                new_value=None,
                changed_by=changed_by,
                reason=reason,
            )

            async with self._versions_lock:
                if runtime_id not in self._versions:
                    self._versions[runtime_id] = []

                # Get current version
                current_version = len(self._versions[runtime_id])

                # Create new version
                version = MetadataVersion(
                    runtime_id=runtime_id,
                    version=current_version + 1,
                    metadata=self._metadata[runtime_id].copy(),
                    changed_by=changed_by,
                    changes=[change],
                )

                self._versions[runtime_id].append(version)

                # Trim old versions if at capacity
                if len(self._versions[runtime_id]) > self._max_versions:
                    self._versions[runtime_id] = self._versions[runtime_id][
                        -self._max_versions :
                    ]

                async with self._metrics_lock:
                    self._metrics["metadata_versions"] += 1

            # Call change callbacks
            for callback in self._on_change:
                try:
                    callback(runtime_id, key, old_value, None)
                except Exception as e:
                    logger.error(f"Error in metadata change callback: {e}")

            if self._enable_logging:
                logger.info(
                    f"Metadata deleted: {runtime_id}.{key} "
                    f"(by: {changed_by}, reason: {reason})"
                )

            return True

    def update(
        self,
        runtime_id: str,
        updates: Dict[str, Any],
        changed_by: str = "",
        reason: str = "",
        validate: bool = True,
    ) -> int:
        """
        Update multiple metadata values for a runtime.

        Args:
            runtime_id: ID of the runtime.
            updates: Dictionary of key-value pairs to update.
            changed_by: Who made the changes.
            reason: Reason for the changes.
            validate: Whether to validate against schema.

        Returns:
            Number of metadata values updated.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> count = metadata_registry.update(
            ...     "memory_runtime",
            ...     {"version": "2.0.0", "config": {"max_size": 2048}}
            ... )
        """
        return asyncio.run(
            self._update_async(runtime_id, updates, changed_by, reason, validate)
        )

    async def _update_async(
        self,
        runtime_id: str,
        updates: Dict[str, Any],
        changed_by: str = "",
        reason: str = "",
        validate: bool = True,
    ) -> int:
        """Async version of update."""
        # Validate against schema if requested
        if validate:
            errors = await self._validate_metadata(runtime_id, updates)
            if errors:
                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageValidationError,
                )

                raise MessageValidationError(
                    f"Metadata validation failed: {', '.join(errors)}",
                    validation_errors=errors,
                )

        count = 0
        changes = []

        async with self._metadata_lock:
            # Initialize metadata for runtime if not exists
            if runtime_id not in self._metadata:
                self._metadata[runtime_id] = {}

            for key, value in updates.items():
                # Get old value
                old_value = self._metadata[runtime_id].get(key)

                # Set new value
                self._metadata[runtime_id][key] = value

                # Record change
                changes.append(
                    MetadataChange(
                        runtime_id=runtime_id,
                        key=key,
                        old_value=old_value,
                        new_value=value,
                        changed_by=changed_by,
                        reason=reason,
                    )
                )

                # Update metrics
                async with self._metrics_lock:
                    if old_value is None:
                        self._metrics["metadata_set"] += 1
                    else:
                        self._metrics["metadata_updated"] += 1

                count += 1

            # Record version
            async with self._versions_lock:
                if runtime_id not in self._versions:
                    self._versions[runtime_id] = []

                # Get current version
                current_version = len(self._versions[runtime_id])

                # Create new version
                version = MetadataVersion(
                    runtime_id=runtime_id,
                    version=current_version + 1,
                    metadata=self._metadata[runtime_id].copy(),
                    changed_by=changed_by,
                    changes=changes,
                )

                self._versions[runtime_id].append(version)

                # Trim old versions if at capacity
                if len(self._versions[runtime_id]) > self._max_versions:
                    self._versions[runtime_id] = self._versions[runtime_id][
                        -self._max_versions :
                    ]

                async with self._metrics_lock:
                    self._metrics["metadata_versions"] += 1

            # Call change callbacks
            for change in changes:
                for callback in self._on_change:
                    try:
                        callback(
                            change.runtime_id,
                            change.key,
                            change.old_value,
                            change.new_value,
                        )
                    except Exception as e:
                        logger.error(f"Error in metadata change callback: {e}")

            if self._enable_logging:
                logger.info(
                    f"Metadata updated: {runtime_id} ({count} keys) "
                    f"(by: {changed_by}, reason: {reason})"
                )

        return count

    def clear(self, runtime_id: str) -> int:
        """
        Clear all metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Number of metadata keys cleared.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> count = metadata_registry.clear("memory_runtime")
        """
        return asyncio.run(self._clear_async(runtime_id))

    async def _clear_async(self, runtime_id: str) -> int:
        """Async version of clear."""
        async with self._metadata_lock:
            if runtime_id not in self._metadata:
                return 0

            count = len(self._metadata[runtime_id])
            self._metadata[runtime_id].clear()

            # Record version
            async with self._versions_lock:
                if runtime_id not in self._versions:
                    self._versions[runtime_id] = []

                # Get current version
                current_version = len(self._versions[runtime_id])

                # Create new version
                version = MetadataVersion(
                    runtime_id=runtime_id,
                    version=current_version + 1,
                    metadata={},
                    changed_by="system",
                    changes=[
                        MetadataChange(
                            runtime_id=runtime_id,
                            key="*",
                            old_value=self._metadata[runtime_id].copy(),
                            new_value=None,
                            changed_by="system",
                            reason="clear",
                        )
                    ],
                )

                self._versions[runtime_id].append(version)

                # Trim old versions if at capacity
                if len(self._versions[runtime_id]) > self._max_versions:
                    self._versions[runtime_id] = self._versions[runtime_id][
                        -self._max_versions :
                    ]

            if self._enable_logging:
                logger.info(f"Metadata cleared: {runtime_id} ({count} keys)")

            return count

    def get_version(
        self, runtime_id: str, version: int
    ) -> Optional[MetadataVersion]:
        """
        Get a specific version of metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.
            version: Version number.

        Returns:
            MetadataVersion if found, None otherwise.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> version = metadata_registry.get_version("memory_runtime", 1)
        """
        async with self._versions_lock:
            if runtime_id not in self._versions:
                return None

            # Version numbers start at 1
            if version < 1 or version > len(self._versions[runtime_id]):
                return None

            return self._versions[runtime_id][version - 1]

    def get_latest_version(self, runtime_id: str) -> Optional[MetadataVersion]:
        """
        Get the latest version of metadata for a runtime.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Latest MetadataVersion if found, None otherwise.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> version = metadata_registry.get_latest_version("memory_runtime")
        """
        async with self._versions_lock:
            if runtime_id not in self._versions:
                return None

            return self._versions[runtime_id][-1] if self._versions[runtime_id] else None

    def list_versions(self, runtime_id: str) -> List[int]:
        """
        List all version numbers for a runtime's metadata.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            List of version numbers.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> versions = metadata_registry.list_versions("memory_runtime")
        """
        async with self._versions_lock:
            if runtime_id not in self._versions:
                return []

            return list(range(1, len(self._versions[runtime_id]) + 1))

    def register_schema(
        self, schema: MetadataSchema
    ) -> None:
        """
        Register a metadata schema.

        Args:
            schema: Schema to register.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> schema = MetadataSchema(
            ...     name="runtime_config",
            ...     required_keys={"version", "type"},
            ...     key_types={"version": str, "type": str}
            ... )
            >>> metadata_registry.register_schema(schema)
        """
        asyncio.run(self._register_schema_async(schema))

    async def _register_schema_async(self, schema: MetadataSchema) -> None:
        """Async version of register_schema."""
        async with self._schemas_lock:
            self._schemas[schema.name] = schema

            if self._enable_logging:
                logger.info(f"Metadata schema registered: {schema.name}")

    def unregister_schema(self, schema_name: str) -> bool:
        """
        Unregister a metadata schema.

        Args:
            schema_name: Name of the schema to unregister.

        Returns:
            True if schema was unregistered, False otherwise.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metadata_registry.unregister_schema("runtime_config")
            True
        """
        return asyncio.run(self._unregister_schema_async(schema_name))

    async def _unregister_schema_async(self, schema_name: str) -> bool:
        """Async version of unregister_schema."""
        async with self._schemas_lock:
            if schema_name in self._schemas:
                del self._schemas[schema_name]

                if self._enable_logging:
                    logger.info(f"Metadata schema unregistered: {schema_name}")
                return True
            return False

    def get_schema(self, schema_name: str) -> Optional[MetadataSchema]:
        """
        Get a metadata schema.

        Args:
            schema_name: Name of the schema.

        Returns:
            MetadataSchema if found, None otherwise.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> schema = metadata_registry.get_schema("runtime_config")
        """
        return self._schemas.get(schema_name)

    def list_schemas(self) -> List[str]:
        """
        List all registered schema names.

        Returns:
            List of schema names.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> schemas = metadata_registry.list_schemas()
        """
        return list(self._schemas.keys())

    async def _validate_metadata(
        self, runtime_id: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Validate metadata against all applicable schemas.

        Args:
            runtime_id: ID of the runtime.
            metadata: Metadata to validate.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Get runtime info to determine applicable schemas
        runtime_info = self._registry.get(runtime_id)
        if runtime_info is None:
            return [f"Runtime not found: {runtime_id}"]

        # Check all schemas
        async with self._schemas_lock:
            for schema in self._schemas.values():
                # Skip if schema doesn't apply to this runtime type
                if schema.name != runtime_info.type and schema.name != "default":
                    continue

                schema_errors = schema.validate(metadata)
                errors.extend(schema_errors)

        # Update metrics
        async with self._metrics_lock:
            self._metrics["validation_errors"] += len(errors)

        return errors

    def on_change(
        self,
        callback: Callable[[str, str, Any, Any], None],
    ) -> None:
        """
        Register a callback for metadata changes.

        Args:
            callback: Callback function to call when metadata changes.
                     Parameters: (runtime_id, key, old_value, new_value)

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> def on_change(runtime_id, key, old_value, new_value):
            ...     print(f"Metadata changed: {runtime_id}.{key}")
            >>> metadata_registry.on_change(on_change)
        """
        self._on_change.append(callback)

    def search(
        self,
        query: Dict[str, Any],
        limit: int = 100,
    ) -> List[str]:
        """
        Search for runtimes matching metadata criteria.

        Args:
            query: Dictionary of key-value pairs to match.
            limit: Maximum number of results.

        Returns:
            List of runtime IDs matching the criteria.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> # Assume some metadata is set
            >>> results = metadata_registry.search({"type": "memory", "version": "1.0.0"})
        """
        results = []

        for runtime_id, metadata in self._metadata.items():
            match = True
            for key, value in query.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break

            if match:
                results.append(runtime_id)
                if len(results) >= limit:
                    break

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metadata registry metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metrics = metadata_registry.get_metrics()
            >>> metrics["metadata_set"]
            0
        """
        return {
            **self._metrics,
            "runtimes_with_metadata": len(self._metadata),
            "total_metadata_keys": sum(
                len(metadata) for metadata in self._metadata.values()
            ),
            "schemas_count": len(self._schemas),
            "versions_count": sum(
                len(versions) for versions in self._versions.values()
            ),
        }

    def clear_all(self) -> int:
        """
        Clear all metadata for all runtimes.

        Returns:
            Number of runtimes cleared.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> count = metadata_registry.clear_all()
        """
        count = len(self._metadata)
        self._metadata.clear()
        self._versions.clear()
        self._metrics = {
            "metadata_set": 0,
            "metadata_get": 0,
            "metadata_updated": 0,
            "metadata_deleted": 0,
            "metadata_versions": 0,
            "validation_errors": 0,
        }
        return count

    def shutdown(self) -> None:
        """
        Shutdown the metadata registry.

        Example:
            >>> metadata_registry = RuntimeMetadataRegistry()
            >>> metadata_registry.shutdown()
        """
        self.clear_all()
        self._schemas.clear()
        self._on_change.clear()

        if self._owns_registry:
            self._registry.shutdown()

        logger.info("Runtime metadata registry shutdown complete")

    def __repr__(self) -> str:
        """Return string representation of the metadata registry."""
        return (
            f"RuntimeMetadataRegistry("
            f"runtimes={len(self._metadata)}, "
            f"keys={sum(len(m) for m in self._metadata.values())}, "
            f"schemas={len(self._schemas)})"
        )
