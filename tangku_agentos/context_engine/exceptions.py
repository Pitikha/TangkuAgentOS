#!/usr/bin/env python3
"""
Custom exceptions for the TangkuAgentOS Context Engine.

This module defines all custom exceptions used throughout the context system
to provide clear error handling and debugging.
"""

from typing import Any, Optional


# =============================================================================
# Base Exception
# =============================================================================


class ContextError(Exception):
    """
    Base exception for all context-related errors.
    
    This is the parent class for all custom exceptions in the context engine.
    All context-specific exceptions should inherit from this class.
    
    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Additional details about the error
        cause: The underlying exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        code: str = "CONTEXT_ERROR",
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
# Context Lifecycle Exceptions
# =============================================================================


class ContextNotFoundError(ContextError):
    """
    Exception raised when a requested context is not found.
    
    This exception is raised when attempting to access a context that doesn't exist
    in the system.
    
    Attributes:
        context_id: The ID of the context that was not found
    """
    
    def __init__(
        self,
        context_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        msg = message or f"Context with ID '{context_id}' not found"
        super().__init__(msg, code="CONTEXT_NOT_FOUND", details=details, cause=cause)


class ContextExistsError(ContextError):
    """
    Exception raised when attempting to create a context that already exists.
    
    This exception is raised when trying to create a context with an ID that
    is already in use.
    
    Attributes:
        context_id: The ID of the context that already exists
    """
    
    def __init__(
        self,
        context_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        msg = message or f"Context with ID '{context_id}' already exists"
        super().__init__(msg, code="CONTEXT_EXISTS", details=details, cause=cause)


class ContextDeletedError(ContextError):
    """
    Exception raised when attempting to access a deleted context.
    
    Attributes:
        context_id: The ID of the deleted context
    """
    
    def __init__(
        self,
        context_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        msg = message or f"Context with ID '{context_id}' has been deleted"
        super().__init__(msg, code="CONTEXT_DELETED", details=details, cause=cause)


# =============================================================================
# Assembly Exceptions
# =============================================================================


class ContextAssemblyError(ContextError):
    """
    Base exception for context assembly errors.
    
    This is the parent class for all assembly-related exceptions.
    
    Attributes:
        source: The source that encountered the error
    """
    
    def __init__(
        self,
        source: str,
        message: str,
        code: str = "ASSEMBLY_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.source = source
        super().__init__(message, code=code, details=details, cause=cause)


class ContextSourceError(ContextAssemblyError):
    """
    Exception raised when a context source fails to provide context.
    
    Attributes:
        source: The source that failed
        source_id: The ID of the source
        query: The query that was attempted
    """
    
    def __init__(
        self,
        source: str,
        source_id: str,
        query: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.source_id = source_id
        self.query = query
        msg = message or f"Context source '{source}' (ID: {source_id}) failed for query: {query}"
        super().__init__(source, msg, code="SOURCE_ERROR", details=details, cause=cause)


class ContextMergeError(ContextAssemblyError):
    """
    Exception raised when merging contexts fails.
    
    Attributes:
        context_ids: List of context IDs that failed to merge
        reason: The reason for the merge failure
    """
    
    def __init__(
        self,
        context_ids: List[str],
        reason: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_ids = context_ids
        self.reason = reason
        msg = message or f"Failed to merge contexts {context_ids}: {reason}"
        super().__init__("merge", msg, code="MERGE_ERROR", details=details, cause=cause)


class ContextDeduplicationError(ContextAssemblyError):
    """
    Exception raised when deduplication fails.
    
    Attributes:
        duplicate_count: Number of duplicates found
        reason: The reason for the deduplication failure
    """
    
    def __init__(
        self,
        duplicate_count: int,
        reason: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.duplicate_count = duplicate_count
        self.reason = reason
        msg = message or f"Deduplication failed for {duplicate_count} duplicates: {reason}"
        super().__init__("deduplication", msg, code="DEDUPLICATION_ERROR", details=details, cause=cause)


# =============================================================================
# Optimization Exceptions
# =============================================================================


class ContextOptimizationError(ContextError):
    """
    Base exception for context optimization errors.
    
    This is the parent class for all optimization-related exceptions.
    """
    
    def __init__(
        self,
        message: str,
        code: str = "OPTIMIZATION_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message, code=code, details=details, cause=cause)


class ContextCompressionError(ContextOptimizationError):
    """
    Exception raised when context compression fails.
    
    Attributes:
        method: The compression method that failed
        original_size: Original size of the context
        target_size: Target size for compression
    """
    
    def __init__(
        self,
        method: str,
        original_size: int,
        target_size: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.method = method
        self.original_size = original_size
        self.target_size = target_size
        msg = message or f"Compression failed with {method}: {original_size} -> {target_size}"
        super().__init__(msg, code="COMPRESSION_ERROR", details=details, cause=cause)


class ContextBudgetError(ContextOptimizationError):
    """
    Exception raised when context budgeting fails.
    
    Attributes:
        budget: The token budget
        actual: The actual token count
        overflow: The number of tokens over the budget
    """
    
    def __init__(
        self,
        budget: int,
        actual: int,
        overflow: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.budget = budget
        self.actual = actual
        self.overflow = overflow
        msg = message or f"Context exceeds budget: {actual}/{budget} (+{overflow})"
        super().__init__(msg, code="BUDGET_ERROR", details=details, cause=cause)


class ContextRankingError(ContextOptimizationError):
    """
    Exception raised when context ranking fails.
    
    Attributes:
        method: The ranking method that failed
        context_count: Number of contexts being ranked
    """
    
    def __init__(
        self,
        method: str,
        context_count: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.method = method
        self.context_count = context_count
        msg = message or f"Ranking failed with {method} for {context_count} contexts"
        super().__init__(msg, code="RANKING_ERROR", details=details, cause=cause)


# =============================================================================
# Cache Exceptions
# =============================================================================


class ContextCacheError(ContextError):
    """
    Base exception for context cache errors.
    
    This is the parent class for all cache-related exceptions.
    
    Attributes:
        cache_level: The cache level that encountered the error
    """
    
    def __init__(
        self,
        cache_level: str,
        message: str,
        code: str = "CACHE_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.cache_level = cache_level
        super().__init__(message, code=code, details=details, cause=cause)


class ContextCacheMissError(ContextCacheError):
    """
    Exception raised when a context is not found in cache.
    
    Attributes:
        context_id: The ID of the context that was not found
        cache_level: The cache level that was checked
    """
    
    def __init__(
        self,
        context_id: str,
        cache_level: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        msg = message or f"Cache miss for context '{context_id}' at level {cache_level}"
        super().__init__(cache_level, msg, code="CACHE_MISS", details=details, cause=cause)


class ContextCacheInvalidationError(ContextCacheError):
    """
    Exception raised when cache invalidation fails.
    
    Attributes:
        context_id: The ID of the context being invalidated
        reason: The reason for invalidation
    """
    
    def __init__(
        self,
        context_id: str,
        reason: str,
        cache_level: str = "all",
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        self.reason = reason
        msg = message or f"Cache invalidation failed for context '{context_id}': {reason}"
        super().__init__(cache_level, msg, code="CACHE_INVALIDATION_ERROR", details=details, cause=cause)


# =============================================================================
# Session Exceptions
# =============================================================================


class ContextSessionError(ContextError):
    """
    Base exception for context session errors.
    
    This is the parent class for all session-related exceptions.
    
    Attributes:
        session_id: The ID of the session that encountered the error
    """
    
    def __init__(
        self,
        session_id: str,
        message: str,
        code: str = "SESSION_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.session_id = session_id
        super().__init__(message, code=code, details=details, cause=cause)


class ContextSessionNotFoundError(ContextSessionError):
    """
    Exception raised when a requested session is not found.
    
    Attributes:
        session_id: The ID of the session that was not found
    """
    
    def __init__(
        self,
        session_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Session with ID '{session_id}' not found"
        super().__init__(session_id, msg, code="SESSION_NOT_FOUND", details=details, cause=cause)


class ContextSessionExistsError(ContextSessionError):
    """
    Exception raised when attempting to create a session that already exists.
    
    Attributes:
        session_id: The ID of the session that already exists
    """
    
    def __init__(
        self,
        session_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Session with ID '{session_id}' already exists"
        super().__init__(session_id, msg, code="SESSION_EXISTS", details=details, cause=cause)


class ContextSessionTimeoutError(ContextSessionError):
    """
    Exception raised when a session times out.
    
    Attributes:
        session_id: The ID of the session that timed out
        timeout: The timeout value that was exceeded
    """
    
    def __init__(
        self,
        session_id: str,
        timeout: float,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.timeout = timeout
        msg = message or f"Session '{session_id}' timed out after {timeout}s"
        super().__init__(session_id, msg, code="SESSION_TIMEOUT", details=details, cause=cause)


# =============================================================================
# Snapshot Exceptions
# =============================================================================


class ContextSnapshotError(ContextError):
    """
    Base exception for context snapshot errors.
    
    This is the parent class for all snapshot-related exceptions.
    
    Attributes:
        snapshot_id: The ID of the snapshot that encountered the error
    """
    
    def __init__(
        self,
        snapshot_id: str,
        message: str,
        code: str = "SNAPSHOT_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.snapshot_id = snapshot_id
        super().__init__(message, code=code, details=details, cause=cause)


class ContextSnapshotNotFoundError(ContextSnapshotError):
    """
    Exception raised when a requested snapshot is not found.
    
    Attributes:
        snapshot_id: The ID of the snapshot that was not found
    """
    
    def __init__(
        self,
        snapshot_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Snapshot with ID '{snapshot_id}' not found"
        super().__init__(snapshot_id, msg, code="SNAPSHOT_NOT_FOUND", details=details, cause=cause)


class ContextSnapshotExistsError(ContextSnapshotError):
    """
    Exception raised when attempting to create a snapshot that already exists.
    
    Attributes:
        snapshot_id: The ID of the snapshot that already exists
    """
    
    def __init__(
        self,
        snapshot_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Snapshot with ID '{snapshot_id}' already exists"
        super().__init__(snapshot_id, msg, code="SNAPSHOT_EXISTS", details=details, cause=cause)


class ContextSnapshotRestoreError(ContextSnapshotError):
    """
    Exception raised when restoring a snapshot fails.
    
    Attributes:
        snapshot_id: The ID of the snapshot being restored
        reason: The reason for the restore failure
    """
    
    def __init__(
        self,
        snapshot_id: str,
        reason: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.reason = reason
        msg = message or f"Failed to restore snapshot '{snapshot_id}': {reason}"
        super().__init__(snapshot_id, msg, code="SNAPSHOT_RESTORE_ERROR", details=details, cause=cause)


# =============================================================================
# Validation Exceptions
# =============================================================================


class ContextValidationError(ContextError):
    """
    Exception raised when context data fails validation.
    
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


class ContextTokenValidationError(ContextValidationError):
    """
    Exception raised when token count validation fails.
    
    Attributes:
        token_count: The actual token count
        max_tokens: The maximum allowed token count
    """
    
    def __init__(
        self,
        token_count: int,
        max_tokens: int,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.token_count = token_count
        self.max_tokens = max_tokens
        msg = message or f"Token count {token_count} exceeds maximum {max_tokens}"
        super().__init__(
            field="token_count",
            value=token_count,
            expected=f"<= {max_tokens}",
            message=msg,
            details=details,
            cause=cause,
        )


class ContextEmptyError(ContextValidationError):
    """
    Exception raised when a context is empty.
    
    Attributes:
        context_id: The ID of the empty context
    """
    
    def __init__(
        self,
        context_id: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Context '{context_id}' is empty"
        super().__init__(
            field="content",
            value=None,
            expected="non-empty content",
            message=msg,
            details=details,
            cause=cause,
        )


# =============================================================================
# Permission and Security Exceptions
# =============================================================================


class ContextPermissionError(ContextError):
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


class ContextAccessDeniedError(ContextPermissionError):
    """
    Exception raised when access to a context is denied.
    
    Attributes:
        context_id: The ID of the context that was accessed
    """
    
    def __init__(
        self,
        context_id: str,
        user: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        msg = message or f"Access denied to context '{context_id}'"
        super().__init__(
            action="access",
            resource=f"context:{context_id}",
            user=user,
            message=msg,
            details=details,
            cause=cause,
        )


class ContextIsolationError(ContextError):
    """
    Exception raised when context isolation is violated.
    
    Attributes:
        context_id: The ID of the context
        violating_context_id: The ID of the context that violated isolation
        reason: The reason for the isolation violation
    """
    
    def __init__(
        self,
        context_id: str,
        violating_context_id: str,
        reason: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.context_id = context_id
        self.violating_context_id = violating_context_id
        self.reason = reason
        msg = message or f"Isolation violation: {context_id} and {violating_context_id} - {reason}"
        super().__init__(msg, code="ISOLATION_ERROR", details=details, cause=cause)


# =============================================================================
# Timeout Exceptions
# =============================================================================


class ContextTimeoutError(ContextError):
    """
    Exception raised when a context operation times out.
    
    Attributes:
        operation: The operation that timed out
        timeout: The timeout value that was exceeded
    """
    
    def __init__(
        self,
        operation: str,
        timeout: float,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
        self.timeout = timeout
        msg = message or f"Context {operation} timed out after {timeout}s"
        super().__init__(msg, code="TIMEOUT_ERROR", details=details, cause=cause)


# =============================================================================
# Provider Exceptions
# =============================================================================


class ContextProviderError(ContextError):
    """
    Base exception for context provider errors.
    
    This is the parent class for all provider-related exceptions.
    
    Attributes:
        provider: The name of the provider that encountered the error
    """
    
    def __init__(
        self,
        provider: str,
        message: str,
        code: str = "PROVIDER_ERROR",
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.provider = provider
        super().__init__(message, code=code, details=details, cause=cause)


class ContextProviderConnectionError(ContextProviderError):
    """
    Exception raised when unable to connect to a context provider.
    
    Attributes:
        provider: The name of the provider
        connection_string: The connection string that failed
    """
    
    def __init__(
        self,
        provider: str,
        connection_string: str,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.connection_string = connection_string
        msg = message or f"Unable to connect to {provider} provider at {connection_string}"
        super().__init__(provider, msg, code="PROVIDER_CONNECTION_ERROR", details=details, cause=cause)


class ContextProviderTimeoutError(ContextProviderError):
    """
    Exception raised when a provider operation times out.
    
    Attributes:
        provider: The name of the provider
        operation: The operation that timed out
        timeout: The timeout value that was exceeded
    """
    
    def __init__(
        self,
        provider: str,
        operation: str,
        timeout: float,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        self.operation = operation
        self.timeout = timeout
        msg = message or f"{provider} provider operation '{operation}' timed out after {timeout}s"
        super().__init__(provider, msg, code="PROVIDER_TIMEOUT_ERROR", details=details, cause=cause)
