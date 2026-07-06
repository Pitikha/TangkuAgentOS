from __future__ import annotations

from .interfaces import PluginInstaller


class PluginInstaller(PluginInstaller):
    """Plugin installer architecture."""

    def install(self, plugin: "Plugin") -> None:
        raise NotImplementedError
