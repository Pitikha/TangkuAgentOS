from __future__ import annotations


class CoreError(Exception):
    """Base exception for the Tangku core runtime."""


class ConfigurationError(CoreError):
    """Raised when configuration cannot be loaded or validated."""


class EventBusError(CoreError):
    """Raised for event dispatch and subscription failures."""


class LoggerError(CoreError):
    """Raised when logging infrastructure fails."""


class RegistryError(CoreError):
    """Raised when registry operations fail."""


class StateError(CoreError):
    """Raised for state management failures."""


class LifecycleError(CoreError):
    """Raised when lifecycle transitions fail."""
