from __future__ import annotations

from .interfaces import PluginRegistryInterface


class PluginRegistry(PluginRegistryInterface):
    """Plugin registry foundation."""

    def register(self, plugin: "Plugin") -> None:
        raise NotImplementedError

    def resolve(self, plugin_id: str) -> "Plugin":
        raise NotImplementedError
