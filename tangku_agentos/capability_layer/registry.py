from __future__ import annotations

from typing import Dict, List

from .interfaces import CapabilityRegistryInterface
from .models import CapabilityMetadata
from .exceptions import CapabilityRegistryError


class CapabilityRegistry(CapabilityRegistryInterface):
    """Registry for capability metadata."""

    def __init__(self) -> None:
        self._metadata: Dict[str, CapabilityMetadata] = {}

    def register(self, metadata: CapabilityMetadata) -> None:
        self._metadata[metadata.name] = metadata

    def unregister(self, capability_name: str) -> None:
        self._metadata.pop(capability_name, None)

    def get(self, capability_name: str) -> CapabilityMetadata:
        capability = self._metadata.get(capability_name)
        if capability is None:
            raise CapabilityRegistryError(f"Capability not found: {capability_name}")
        return capability

    def list(self) -> list[CapabilityMetadata]:
        return list(self._metadata.values())
