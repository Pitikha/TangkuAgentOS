from __future__ import annotations

from .interfaces import PluginPackageManager


class PluginPackageManager(PluginPackageManager):
    """Plugin package manager architecture."""

    def package(self, plugin: "Plugin") -> str:
        raise NotImplementedError

    def install_package(self, package_path: str) -> "Plugin":
        raise NotImplementedError
