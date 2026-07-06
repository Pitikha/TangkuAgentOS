from __future__ import annotations

from .exceptions import CapabilityManagerError
from .interfaces import CapabilityManagerInterface
from .models import CapabilityMetadata
from .registry import CapabilityRegistry


class CapabilityManager(CapabilityManagerInterface):
    """Manager for registering and querying capabilities."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def register_capability(self, metadata: CapabilityMetadata) -> None:
        self._registry.register(metadata)

    def unregister_capability(self, capability_name: str) -> None:
        self._registry.unregister(capability_name)

    def get_capability(self, capability_name: str) -> CapabilityMetadata:
        return self._registry.get(capability_name)

    def list_capabilities(self) -> list[CapabilityMetadata]:
        return self._registry.list()
