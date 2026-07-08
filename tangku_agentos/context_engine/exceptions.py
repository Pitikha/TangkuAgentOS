from __future__ import annotations


class ContextEngineError(Exception):
    """Base context engine error."""


class ContextRegistryError(ContextEngineError):
    """Raised when context registry operations fail."""


class ContextManagerError(ContextEngineError):
    """Raised when context manager operations fail."""


class ContextResolverError(ContextEngineError):
    """Raised when context resolution fails."""


class ContextSnapshotError(ContextEngineError):
    """Raised when snapshot operations fail."""
