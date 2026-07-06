from __future__ import annotations

from .interfaces import PluginLifecycleManager


class PluginLifecycleManager(PluginLifecycleManager):
    """Plugin lifecycle manager architecture."""

    def activate(self, plugin_id: str) -> None:
        raise NotImplementedError

    def deactivate(self, plugin_id: str) -> None:
        raise NotImplementedError
