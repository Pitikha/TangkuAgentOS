from __future__ import annotations

from .interfaces import PluginResolver


class PluginResolver(PluginResolver):
    """Plugin resolver architecture."""

    def resolve(self, plugin_id: str) -> "Plugin":
        raise NotImplementedError
