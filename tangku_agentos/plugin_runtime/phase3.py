from __future__ import annotations

from typing import Any


class PluginRegistry:
    """Minimal plugin registry supporting discovery, install, resolve, and lifecycle states."""

    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, Any]] = {}

    def discover(self, definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for definition in definitions:
            self._plugins[definition["name"]] = {
                "name": definition["name"],
                "version": definition.get("version", "0.1.0"),
                "dependencies": definition.get("dependencies", []),
                "state": "discovered",
            }
        return list(self._plugins.values())

    def install(self, plugin_name: str) -> dict[str, Any] | None:
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return None
        plugin["state"] = "installed"
        return plugin

    def resolve(self, plugin_name: str) -> dict[str, Any] | None:
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            return None
        return dict(plugin)
