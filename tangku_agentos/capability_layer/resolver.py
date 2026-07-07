from __future__ import annotations

from .exceptions import CapabilityResolverError
from .interfaces import CapabilityResolver
from .models import CapabilityMetadata, CapabilityRequest
from .registry import CapabilityRegistry


class CapabilityResolverImpl(CapabilityResolver):
    """Foundation capability resolver."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def resolve(self, request: CapabilityRequest) -> CapabilityMetadata:
        try:
            return self._registry.get(request.capability_name)
        except Exception as error:
            raise CapabilityResolverError(str(error)) from error
