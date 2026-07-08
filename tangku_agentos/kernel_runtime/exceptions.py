"""Custom exceptions for TangkuAgentOS kernel runtime.

This module defines all custom exceptions raised by the kernel runtime system,
including errors for runtime management, dependency resolution, and configuration.
"""

from __future__ import annotations


class KernelError(Exception):
    """Base exception for kernel runtime errors.

    This is the root exception class for all errors raised by the kernel runtime.
    """

    pass


class RuntimeError(KernelError):
    """Raised when a runtime operation fails.

    This exception is raised when a runtime cannot be started, stopped, or managed.
    """

    pass


class RuntimeRegistrationError(KernelError):
    """Raised when runtime registration fails.

    This exception is raised when a runtime cannot be registered due to
    invalid input, duplicate ID, or other registration issues.
    """

    pass


class RuntimeResolutionError(KernelError):
    """Raised when runtime resolution fails.

    This exception is raised when a runtime cannot be resolved or instantiated.
    """

    pass


class DependencyError(KernelError):
    """Raised when dependency resolution fails.

    This exception is raised when runtime dependencies cannot be resolved
    or when there is a circular dependency.
    """

    pass


class ConfigurationError(KernelError):
    """Raised when kernel configuration is invalid or cannot be loaded.

    This exception is raised when configuration files are missing, invalid,
    or contain errors.
    """

    pass


class SchedulerError(KernelError):
    """Raised when scheduling operations fail.

    This exception is raised when a runtime, agent, workflow, or task cannot
    be scheduled for execution.
    """

    pass


class ResourceError(KernelError):
    """Raised when resource management fails.

    This exception is raised when resources cannot be allocated, released,
    or managed.
    """

    pass


class RecoveryError(KernelError):
    """Raised when runtime recovery fails.

    This exception is raised when a failed runtime cannot be recovered.
    """

    pass
