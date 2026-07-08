from __future__ import annotations


class MemoryEngineError(Exception):
    """Base memory engine exception."""


class MemoryRegistryError(MemoryEngineError):
    """Raised when memory registry operations fail."""


class MemoryManagerError(MemoryEngineError):
    """Raised when memory manager operations fail."""


class MemoryProviderError(MemoryEngineError):
    """Raised when memory provider operations fail."""


class MemoryResolverError(MemoryEngineError):
    """Raised when memory resolver operations fail."""
