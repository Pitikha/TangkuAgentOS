from __future__ import annotations


class CapabilityLayerError(Exception):
    """Base capability layer error."""


class CapabilityRegistryError(CapabilityLayerError):
    """Raised when capability registry operations fail."""


class CapabilityResolverError(CapabilityLayerError):
    """Raised when capability resolution fails."""


class CapabilityDispatcherError(CapabilityLayerError):
    """Raised when capability dispatching fails."""


class CapabilityManagerError(CapabilityLayerError):
    """Raised when capability manager operations fail."""
