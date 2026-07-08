"""
Runtime Communication Framework - Exception Definitions

This module defines all custom exceptions used in the TangkuAgentOS communication framework.
Each exception provides detailed error information for proper error handling and debugging.

Exception Hierarchy:
- MessageError: Base exception for all message-related errors
  - MessageDeliveryError: Failed to deliver a message
  - MessageTimeoutError: Message operation timed out
  - MessageValidationError: Message validation failed
  - DuplicateMessageError: Duplicate message detected
  - CircuitBreakerOpenError: Circuit breaker is open
  - AuthorizationError: Authorization failed
  - RuntimeNotFoundError: Runtime not found
  - RuntimeNotAvailableError: Runtime is not available

Author: TangkuAgentOS Team
License: MIT
"""

from typing import Any, Optional, Dict


class MessageError(Exception):
    """
    Base exception for all message-related errors in the communication framework.
    
    This is the root exception class for all communication-related errors.
    All other communication exceptions inherit from this class.
    
    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Additional error details
        context: Context information (message IDs, runtime IDs, etc.)
    
    Example:
        >>> try:
        ...     bus.send(message)
        ... except MessageError as e:
        ...     print(f"Error: {e.code} - {e.message}")
        ...     print(f"Details: {e.details}")
    """
    
    def __init__(
        self,
        message: str,
        code: str = "MESSAGE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.context = context or {}
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"{self.code}: {self.message}"
    
    def __repr__(self) -> str:
        """Return detailed representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r}, "
            f"context={self.context!r})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary representation.
        
        Returns:
            Dictionary containing all exception fields
        """
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "context": self.context,
        }


class MessageDeliveryError(MessageError):
    """
    Exception raised when a message fails to be delivered.
    
    This exception is raised when the message bus cannot deliver a message
    to its intended recipient, or when all delivery attempts have failed.
    
    Attributes:
        message_id: ID of the message that failed to deliver
        recipient_id: ID of the recipient that couldn't be reached
        delivery_attempts: Number of delivery attempts made
        last_error: The last error that occurred during delivery
    
    Example:
        >>> try:
        ...     await bus.send(message)
        ... except MessageDeliveryError as e:
        ...     print(f"Failed to deliver message {e.message_id} to {e.recipient_id}")
    """
    
    def __init__(
        self,
        message: str,
        message_id: str = "",
        recipient_id: str = "",
        delivery_attempts: int = 0,
        last_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="MESSAGE_DELIVERY_ERROR",
            details=details,
            context={
                "message_id": message_id,
                "recipient_id": recipient_id,
                "delivery_attempts": delivery_attempts,
                "last_error": last_error,
                **(context or {}),
            }
        )
        self.message_id = message_id
        self.recipient_id = recipient_id
        self.delivery_attempts = delivery_attempts
        self.last_error = last_error


class MessageTimeoutError(MessageError):
    """
    Exception raised when a message operation times out.
    
    This exception is raised when a synchronous operation (like request/response)
    exceeds its timeout period.
    
    Attributes:
        message_id: ID of the message that timed out
        operation: Type of operation that timed out
        timeout: Timeout value that was exceeded
    
    Example:
        >>> try:
        ...     response = await bus.request(query, timeout=5.0)
        ... except MessageTimeoutError as e:
        ...     print(f"Request {e.message_id} timed out after {e.timeout}s")
    """
    
    def __init__(
        self,
        message: str,
        message_id: str = "",
        operation: str = "request",
        timeout: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="MESSAGE_TIMEOUT_ERROR",
            details=details,
            context={
                "message_id": message_id,
                "operation": operation,
                "timeout": timeout,
                **(context or {}),
            }
        )
        self.message_id = message_id
        self.operation = operation
        self.timeout = timeout


class MessageValidationError(MessageError):
    """
    Exception raised when message validation fails.
    
    This exception is raised when a message fails schema validation,
    type checking, or other validation rules.
    
    Attributes:
        message_id: ID of the invalid message
        validation_errors: List of validation error messages
        schema: Name of the schema that failed validation
    
    Example:
        >>> try:
        ...     bus.validate(message)
        ... except MessageValidationError as e:
        ...     print(f"Message {e.message_id} validation failed: {e.validation_errors}")
    """
    
    def __init__(
        self,
        message: str,
        message_id: str = "",
        validation_errors: Optional[list] = None,
        schema: str = "",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="MESSAGE_VALIDATION_ERROR",
            details=details,
            context={
                "message_id": message_id,
                "validation_errors": validation_errors or [],
                "schema": schema,
                **(context or {}),
            }
        )
        self.message_id = message_id
        self.validation_errors = validation_errors or []
        self.schema = schema


class AuthorizationError(MessageError):
    """
    Exception raised when authorization fails.
    
    This exception is raised when a runtime or user is not authorized
    to perform a specific operation or access a resource.
    
    Attributes:
        runtime_id: ID of the runtime that was denied
        operation: Operation that was attempted
        required_permissions: Permissions required for the operation
        user_permissions: Permissions the user/runtime has
    
    Example:
        >>> try:
        ...     bus.send(command)
        ... except AuthorizationError as e:
        ...     print(f"Runtime {e.runtime_id} not authorized for {e.operation}")
    """
    
    def __init__(
        self,
        message: str,
        runtime_id: str = "",
        operation: str = "",
        required_permissions: Optional[list] = None,
        user_permissions: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details=details,
            context={
                "runtime_id": runtime_id,
                "operation": operation,
                "required_permissions": required_permissions or [],
                "user_permissions": user_permissions or [],
                **(context or {}),
            }
        )
        self.runtime_id = runtime_id
        self.operation = operation
        self.required_permissions = required_permissions or []
        self.user_permissions = user_permissions or []


class CircuitBreakerOpenError(MessageError):
    """
    Exception raised when a circuit breaker is open.
    
    This exception is raised when the circuit breaker pattern prevents
    an operation from being executed due to previous failures.
    
    Attributes:
        circuit_breaker_name: Name of the circuit breaker
        state: Current state of the circuit breaker
        failure_count: Number of failures that opened the circuit
        next_attempt: When the next attempt can be made
    
    Example:
        >>> try:
        ...     await bus.send(message)
        ... except CircuitBreakerOpenError as e:
        ...     print(f"Circuit breaker {e.circuit_breaker_name} is open")
        ...     print(f"Next attempt in {e.next_attempt} seconds")
    """
    
    def __init__(
        self,
        message: str,
        circuit_breaker_name: str = "",
        state: str = "open",
        failure_count: int = 0,
        next_attempt: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="CIRCUIT_BREAKER_OPEN_ERROR",
            details=details,
            context={
                "circuit_breaker_name": circuit_breaker_name,
                "state": state,
                "failure_count": failure_count,
                "next_attempt": next_attempt,
                **(context or {}),
            }
        )
        self.circuit_breaker_name = circuit_breaker_name
        self.state = state
        self.failure_count = failure_count
        self.next_attempt = next_attempt


class DuplicateMessageError(MessageError):
    """
    Exception raised when a duplicate message is detected.
    
    This exception is raised when the idempotency or deduplication
    mechanism detects that a message has already been processed.
    
    Attributes:
        message_id: ID of the duplicate message
        original_message_id: ID of the original message
        deduplication_key: Key used for deduplication
    
    Example:
        >>> try:
        ...     await bus.send(message)
        ... except DuplicateMessageError as e:
        ...     print(f"Duplicate message detected: {e.message_id}")
    """
    
    def __init__(
        self,
        message: str,
        message_id: str = "",
        original_message_id: str = "",
        deduplication_key: str = "",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="DUPLICATE_MESSAGE_ERROR",
            details=details,
            context={
                "message_id": message_id,
                "original_message_id": original_message_id,
                "deduplication_key": deduplication_key,
                **(context or {}),
            }
        )
        self.message_id = message_id
        self.original_message_id = original_message_id
        self.deduplication_key = deduplication_key


class RuntimeNotFoundError(MessageError):
    """
    Exception raised when a runtime is not found.
    
    This exception is raised when attempting to communicate with a runtime
    that doesn't exist or hasn't been registered.
    
    Attributes:
        runtime_id: ID of the runtime that was not found
        operation: Operation that was attempted
    
    Example:
        >>> try:
        ...     await bus.send_to("unknown_runtime", message)
        ... except RuntimeNotFoundError as e:
        ...     print(f"Runtime {e.runtime_id} not found")
    """
    
    def __init__(
        self,
        message: str,
        runtime_id: str = "",
        operation: str = "",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="RUNTIME_NOT_FOUND_ERROR",
            details=details,
            context={
                "runtime_id": runtime_id,
                "operation": operation,
                **(context or {}),
            }
        )
        self.runtime_id = runtime_id
        self.operation = operation


class RuntimeNotAvailableError(MessageError):
    """
    Exception raised when a runtime is not available.
    
    This exception is raised when a runtime exists but is not currently
    available (e.g., stopped, paused, or in an error state).
    
    Attributes:
        runtime_id: ID of the runtime that is not available
        runtime_status: Current status of the runtime
        operation: Operation that was attempted
        retry_after: Suggested time to retry (in seconds)
    
    Example:
        >>> try:
        ...     await bus.send_to("paused_runtime", message)
        ... except RuntimeNotAvailableError as e:
        ...     print(f"Runtime {e.runtime_id} is {e.runtime_status}")
        ...     print(f"Retry after {e.retry_after} seconds")
    """
    
    def __init__(
        self,
        message: str,
        runtime_id: str = "",
        runtime_status: str = "",
        operation: str = "",
        retry_after: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="RUNTIME_NOT_AVAILABLE_ERROR",
            details=details,
            context={
                "runtime_id": runtime_id,
                "runtime_status": runtime_status,
                "operation": operation,
                "retry_after": retry_after,
                **(context or {}),
            }
        )
        self.runtime_id = runtime_id
        self.runtime_status = runtime_status
        self.operation = operation
        self.retry_after = retry_after


class RuntimeCommunicationError(MessageError):
    """
    Exception raised for general runtime communication errors.
    
    This is a catch-all exception for runtime communication errors that
    don't fit into more specific categories.
    
    Attributes:
        runtime_id: ID of the runtime involved
        operation: Operation that was attempted
    """
    
    def __init__(
        self,
        message: str,
        runtime_id: str = "",
        operation: str = "",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="RUNTIME_COMMUNICATION_ERROR",
            details=details,
            context={
                "runtime_id": runtime_id,
                "operation": operation,
                **(context or {}),
            }
        )
        self.runtime_id = runtime_id
        self.operation = operation


class SerializationError(MessageError):
    """
    Exception raised when message serialization or deserialization fails.
    
    Attributes:
        message_type: Type of message being serialized
        serialization_format: Format being used (json, msgpack, etc.)
        original_error: The original serialization error
    """
    
    def __init__(
        self,
        message: str,
        message_type: str = "",
        serialization_format: str = "",
        original_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="SERIALIZATION_ERROR",
            details=details,
            context={
                "message_type": message_type,
                "serialization_format": serialization_format,
                "original_error": original_error,
                **(context or {}),
            }
        )
        self.message_type = message_type
        self.serialization_format = serialization_format
        self.original_error = original_error


class DeserializationError(MessageError):
    """
    Exception raised when message deserialization fails.
    
    Attributes:
        data: The data that failed to deserialize
        expected_type: The expected message type
        serialization_format: Format being used
    """
    
    def __init__(
        self,
        message: str,
        data: str = "",
        expected_type: str = "",
        serialization_format: str = "",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="DESERIALIZATION_ERROR",
            details=details,
            context={
                "data": data[:100] + "..." if len(data) > 100 else data,  # Truncate long data
                "expected_type": expected_type,
                "serialization_format": serialization_format,
                **(context or {}),
            }
        )
        self.data = data
        self.expected_type = expected_type
        self.serialization_format = serialization_format
