from __future__ import annotations

from .interfaces import PluginLoader


class PluginLoader(PluginLoader):
    """Plugin loader architecture."""

    def load(self, manifest: "PluginManifest") -> "Plugin":
        raise NotImplementedError
