from __future__ import annotations

from typing import Dict

from .interfaces import InterfaceAdapter, InterfaceRegistryInterface


class InterfaceRegistry(InterfaceRegistryInterface):
    """Registry for interface implementations."""

    def __init__(self) -> None:
        self._interfaces: Dict[str, InterfaceAdapter] = {}

    def register(self, interface_id: str, interface: InterfaceAdapter) -> None:
        self._interfaces[interface_id] = interface

    def resolve(self, interface_id: str) -> InterfaceAdapter:
        return self._interfaces[interface_id]

    def list_registered(self) -> list[str]:
        return list(self._interfaces.keys())
