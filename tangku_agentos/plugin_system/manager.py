from __future__ import annotations

from .interfaces import PluginManagerInterface


class PluginManager(PluginManagerInterface):
    """Plugin manager foundation."""

    def register_plugin(self, plugin: "Plugin") -> None:
        raise NotImplementedError

    def get_plugin(self, plugin_id: str) -> "Plugin":
        raise NotImplementedError

    def list_plugins(self) -> list["Plugin"]:
        raise NotImplementedError

    def uninstall_plugin(self, plugin_id: str) -> None:
        raise NotImplementedError
