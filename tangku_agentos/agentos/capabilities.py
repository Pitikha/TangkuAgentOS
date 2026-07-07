from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .constants import CapabilityType
from .types import AgentMetadata


@dataclass(frozen=True)
class AgentCapability:
    name: str
    description: str
    capability_type: CapabilityType = CapabilityType.CORE
    metadata: AgentMetadata = field(default_factory=dict)


class CapabilityRegistry:
    """Registry for agent capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, AgentCapability] = {}

    def register(self, capability: AgentCapability) -> None:
        self._capabilities[capability.name] = capability

    def resolve(self, name: str) -> AgentCapability:
        capability = self._capabilities.get(name)
        if capability is None:
            raise KeyError(f"Capability not found: {name}")
        return capability

    def list(self) -> list[AgentCapability]:
        return list(self._capabilities.values())
