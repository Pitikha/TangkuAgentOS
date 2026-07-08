#!/usr/bin/env python3
"""
Custom exceptions for the TangkuAgentOS Memory Engine.

This module defines all custom exceptions used throughout the memory system
to provide clear error handling and debugging.
"""

from typing import Any, Optional


# =============================================================================
# Base Exception
# =============================================================================


class MemoryError(Exception):
    """
    Base exception for all memory-related errors.
    
    This is the parent class for all custom exceptions in the memory engine.
    All memory-specific exceptions should inherit from this class.
    
    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Additional details about the error
        cause: The underlying exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        code: str = "MEMORY_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        
        # Build the full error message
        self.full_message = self._build_full_message()
    
    def _build_full_message(self) -> str:
        """Build a detailed error message."""
        parts = [f"[{self.code}] {self.message}"]
        
        if self.details:
            parts.append(f"Details: {self.details}")
        
        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")
        
        return " | ".join(parts)
    
    def __str__(self) -> str:
        return self.full_message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# =============================================================================
# Memory Lifecycle Exceptions
# =============================================================================


class MemoryNotFoundError(MemoryError):
    """
    Exception raised when a requested memory is not found.
    
    This exception is raised when attempting to access a memory that doesn't exist
    in the storage system.
    
    Attributes:
        memory_id: The ID of the memory that was not found
    """
    
    def __init__(
        self,
        memory_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_id = memory_id
        msg = message or f"Memory with ID '{memory_id}' not found"
        super().__init__(msg, code="MEMORY_NOT_FOUND", details=details, cause=cause)


class MemoryExistsError(MemoryError):
    """
    Exception raised when attempting to create a memory that already exists.
    
    This exception is raised when trying to create a memory with an ID that
    is already in use.
    
    Attributes:
        memory_id: The ID of the memory that already exists
    """
    
    def __init__(
        self,
        memory_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_id = memory_id
        msg = message or f"Memory with ID '{memory_id}' already exists"
        super().__init__(msg, code="MEMORY_EXISTS", details=details, cause=cause)


class MemoryDeletedError(MemoryError):
    """
    Exception raised when attempting to access a deleted memory.
    
    Attributes:
        memory_id: The ID of the deleted memory
    """
    
    def __init__(
        self,
        memory_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_id = memory_id
        msg = message or f"Memory with ID '{memory_id}' has been deleted"
        super().__init__(msg, code="MEMORY_DELETED", details=details, cause=cause)


# =============================================================================
# Storage Backend Exceptions
# =============================================================================


class MemoryBackendError(MemoryError):
    """
    Base exception for storage backend errors.
    
    This is the parent class for all backend-specific exceptions.
    
    Attributes:
        backend: The name of the backend that encountered the error
    """
    
    def __init__(
        self,
        backend: str,
        message: str,
        code: str = "BACKEND_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.backend = backend
        super().__init__(message, code=code, details=details, cause=cause)


class MemoryBackendConnectionError(MemoryBackendError):
    """
    Exception raised when unable to connect to a storage backend.
    
    Attributes:
        backend: The name of the backend
        connection_string: The connection string that failed
    """
    
    def __init__(
        self,
        backend: str,
        connection_string: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.connection_string = connection_string
        msg = message or f"Unable to connect to {backend} backend at {connection_string}"
        super().__init__(
            backend, msg, code="BACKEND_CONNECTION_ERROR", details=details, cause=cause
        )


class MemoryBackendTimeoutError(MemoryBackendError):
    """
    Exception raised when a backend operation times out.
    
    Attributes:
        backend: The name of the backend
        operation: The operation that timed out
        timeout: The timeout value that was exceeded
    """
    
    def __init__(
        self,
        backend: str,
        operation: str,
        timeout: float,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
        self.timeout = timeout
        msg = message or f"{backend} backend operation '{operation}' timed out after {timeout}s"
        super().__init__(
            backend, msg, code="BACKEND_TIMEOUT_ERROR", details=details, cause=cause
        )


class MemoryBackendUnavailableError(MemoryBackendError):
    """
    Exception raised when a backend is temporarily unavailable.
    
    Attributes:
        backend: The name of the backend
        retry_after: Suggested time to wait before retrying (in seconds)
    """
    
    def __init__(
        self,
        backend: str,
        retry_after: Optional[float] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.retry_after = retry_after
        msg = message or f"{backend} backend is temporarily unavailable"
        if retry_after:
            msg += f", retry after {retry_after}s"
        super().__init__(
            backend, msg, code="BACKEND_UNAVAILABLE", details=details, cause=cause
        )


# =============================================================================
# Validation Exceptions
# =============================================================================


class MemoryValidationError(MemoryError):
    """
    Exception raised when memory data fails validation.
    
    Attributes:
        field: The field that failed validation
        value: The invalid value
        expected: Description of what was expected
    """
    
    def __init__(
        self,
        field: str,
        value: Any,
        expected: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.field = field
        self.value = value
        self.expected = expected
        msg = message or f"Invalid value for '{field}': {value!r}. Expected: {expected}"
        super().__init__(msg, code="VALIDATION_ERROR", details=details, cause=cause)


class MemorySizeError(MemoryValidationError):
    """
    Exception raised when a memory exceeds size limits.
    
    Attributes:
        size: The actual size of the memory
        max_size: The maximum allowed size
    """
    
    def __init__(
        self,
        size: int,
        max_size: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.size = size
        self.max_size = max_size
        msg = message or f"Memory size {size} exceeds maximum allowed size {max_size}"
        super().__init__(
            field="size",
            value=size,
            expected=f"<= {max_size}",
            message=msg,
            details=details,
            cause=cause,
        )


class MemoryTypeError(MemoryValidationError):
    """
    Exception raised when an invalid memory type is specified.
    
    Attributes:
        memory_type: The invalid memory type
        valid_types: List of valid memory types
    """
    
    def __init__(
        self,
        memory_type: str,
        valid_types: list,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_type = memory_type
        self.valid_types = valid_types
        msg = message or f"Invalid memory type '{memory_type}'. Valid types: {valid_types}"
        super().__init__(
            field="memory_type",
            value=memory_type,
            expected=f"one of {valid_types}",
            message=msg,
            details=details,
            cause=cause,
        )


# =============================================================================
# Permission and Security Exceptions
# =============================================================================


class MemoryPermissionError(MemoryError):
    """
    Exception raised when a permission check fails.
    
    Attributes:
        action: The action that was attempted
        resource: The resource the action was attempted on
        user: The user attempting the action
        required_permission: The permission that was required
    """
    
    def __init__(
        self,
        action: str,
        resource: str,
        user: Optional[str] = None,
        required_permission: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.action = action
        self.resource = resource
        self.user = user
        self.required_permission = required_permission
        msg = message or f"Permission denied for {action} on {resource}"
        if user:
            msg += f" by {user}"
        if required_permission:
            msg += f", requires: {required_permission}"
        super().__init__(msg, code="PERMISSION_ERROR", details=details, cause=cause)


class MemoryAccessDeniedError(MemoryPermissionError):
    """
    Exception raised when access to a memory is denied.
    
    Attributes:
        memory_id: The ID of the memory that was accessed
    """
    
    def __init__(
        self,
        memory_id: str,
        user: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_id = memory_id
        msg = message or f"Access denied to memory '{memory_id}'"
        super().__init__(
            action="access",
            resource=f"memory:{memory_id}",
            user=user,
            message=msg,
            details=details,
            cause=cause,
        )


class MemoryEncryptionError(MemoryError):
    """
    Exception raised when encryption or decryption fails.
    
    Attributes:
        operation: The encryption operation that failed
        algorithm: The encryption algorithm used
    """
    
    def __init__(
        self,
        operation: str,
        algorithm: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
        self.algorithm = algorithm
        msg = message or f"{operation} failed with {algorithm} encryption"
        super().__init__(msg, code="ENCRYPTION_ERROR", details=details, cause=cause)


# =============================================================================
# Transaction and Conflict Exceptions
# =============================================================================


class MemoryTransactionError(MemoryError):
    """
    Exception raised when a transaction fails.
    
    Attributes:
        transaction_id: The ID of the failed transaction
        operations: List of operations in the transaction
        failed_operation: The operation that failed
    """
    
    def __init__(
        self,
        transaction_id: str,
        operations: list,
        failed_operation: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.transaction_id = transaction_id
        self.operations = operations
        self.failed_operation = failed_operation
        msg = message or f"Transaction {transaction_id} failed at operation: {failed_operation}"
        super().__init__(msg, code="TRANSACTION_ERROR", details=details, cause=cause)


class MemoryConflictError(MemoryError):
    """
    Exception raised when a conflict occurs (e.g., version conflict).
    
    Attributes:
        memory_id: The ID of the memory with the conflict
        current_version: The current version of the memory
        expected_version: The expected version for the operation
    """
    
    def __init__(
        self,
        memory_id: str,
        current_version: int,
        expected_version: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.memory_id = memory_id
        self.current_version = current_version
        self.expected_version = expected_version
        msg = message or (
            f"Version conflict for memory '{memory_id}': "
            f"current={current_version}, expected={expected_version}"
        )
        super().__init__(msg, code="CONFLICT_ERROR", details=details, cause=cause)


# =============================================================================
# Embedding and Vector Exceptions
# =============================================================================


class MemoryEmbeddingError(MemoryError):
    """
    Exception raised when embedding generation fails.
    
    Attributes:
        provider: The embedding provider that failed
        model: The embedding model that failed
    """
    
    def __init__(
        self,
        provider: str,
        model: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.provider = provider
        self.model = model
        msg = message or f"Failed to generate embedding with {provider}/{model}"
        super().__init__(msg, code="EMBEDDING_ERROR", details=details, cause=cause)


class MemoryVectorError(MemoryError):
    """
    Exception raised when vector operations fail.
    
    Attributes:
        operation: The vector operation that failed
        dimension: The dimension of the vectors
    """
    
    def __init__(
        self,
        operation: str,
        dimension: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
        self.dimension = dimension
        msg = message or f"Vector {operation} failed for dimension {dimension}"
        super().__init__(msg, code="VECTOR_ERROR", details=details, cause=cause)


# =============================================================================
# Cache Exceptions
# =============================================================================


class MemoryCacheError(MemoryError):
    """
    Exception raised when cache operations fail.
    
    Attributes:
        cache_level: The cache level that encountered the error
    """
    
    def __init__(
        self,
        cache_level: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.cache_level = cache_level
        msg = message or f"Cache error at level {cache_level}"
        super().__init__(msg, code="CACHE_ERROR", details=details, cause=cause)


# =============================================================================
# Snapshot and Backup Exceptions
# =============================================================================


class MemorySnapshotError(MemoryError):
    """
    Exception raised when snapshot operations fail.
    
    Attributes:
        snapshot_id: The ID of the snapshot that encountered the error
        operation: The snapshot operation that failed
    """
    
    def __init__(
        self,
        snapshot_id: str,
        operation: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.snapshot_id = snapshot_id
        self.operation = operation
        msg = message or f"Snapshot {operation} failed for {snapshot_id}"
        super().__init__(msg, code="SNAPSHOT_ERROR", details=details, cause=cause)


class MemoryBackupError(MemoryError):
    """
    Exception raised when backup operations fail.
    
    Attributes:
        backup_id: The ID of the backup that encountered the error
        operation: The backup operation that failed
    """
    
    def __init__(
        self,
        backup_id: str,
        operation: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.backup_id = backup_id
        self.operation = operation
        msg = message or f"Backup {operation} failed for {backup_id}"
        super().__init__(msg, code="BACKUP_ERROR", details=details, cause=cause)


class MemoryRestoreError(MemoryError):
    """
    Exception raised when restore operations fail.
    
    Attributes:
        backup_id: The ID of the backup being restored
        reason: The reason for the restore failure
    """
    
    def __init__(
        self,
        backup_id: str,
        reason: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.backup_id = backup_id
        self.reason = reason
        msg = message or f"Restore from backup {backup_id} failed: {reason}"
        super().__init__(msg, code="RESTORE_ERROR", details=details, cause=cause)
