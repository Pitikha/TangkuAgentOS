from __future__ import annotations


class CoreError(Exception):
    """Base exception for the Tangku core runtime."""


# --- Configuration Exceptions ---
class ConfigurationError(CoreError):
    """Raised when configuration cannot be loaded or validated."""


class SchemaValidationError(ConfigurationError):
    """Raised when configuration schema validation fails."""


class MissingRequiredKeyError(ConfigurationError):
    """Raised when a required configuration key is missing."""


# --- Event Bus Exceptions ---
class EventBusError(CoreError):
    """Raised for event dispatch and subscription failures."""


class EventHandlerError(EventBusError):
    """Raised when an event handler fails."""


class MiddlewareError(EventBusError):
    """Raised when middleware processing fails."""


class EventReplayError(EventBusError):
    """Raised when event replay fails."""


class DeadLetterQueueError(EventBusError):
    """Raised when dead-letter queue operations fail."""


# --- Logger Exceptions ---
class LoggerError(CoreError):
    """Raised when logging infrastructure fails."""


class LogHandlerError(LoggerError):
    """Raised when a log handler fails."""


class LogRotationError(LoggerError):
    """Raised when log rotation fails."""


# --- Registry Exceptions ---
class RegistryError(CoreError):
    """Raised when registry operations fail."""


class DuplicateRegistryKeyError(RegistryError):
    """Raised when a registry key is duplicated."""


class RegistryKeyNotFoundError(RegistryError):
    """Raised when a registry key is not found."""


class TTLExpiredError(RegistryError):
    """Raised when a registry entry's TTL expires."""


class LazyLoadingError(RegistryError):
    """Raised when lazy loading fails."""


# --- State Manager Exceptions ---
class StateError(CoreError):
    """Raised for state management failures."""


class StateKeyNotFoundError(StateError):
    """Raised when a state key is not found."""


class TransactionError(StateError):
    """Raised when a transaction fails."""


class RollbackError(StateError):
    """Raised when a rollback fails."""


class StorageError(StateError):
    """Raised when storage operations fail."""


class SerializationError(StateError):
    """Raised when serialization/deserialization fails."""


# --- Lifecycle Exceptions ---
class LifecycleError(CoreError):
    """Raised when lifecycle transitions fail."""


class LifecycleTimeoutError(LifecycleError):
    """Raised when a lifecycle transition times out."""


class LifecycleRollbackError(LifecycleError):
    """Raised when lifecycle rollback fails."""


class HealthCheckError(LifecycleError):
    """Raised when a health check fails."""
