from __future__ import annotations

from .interfaces import PluginPermissionManager


class PluginPermissionManager(PluginPermissionManager):
    """Plugin permission manager architecture."""

    def authorize(self, plugin_id: str, action: str) -> bool:
        raise NotImplementedError
