from __future__ import annotations

from threading import RLock
from typing import Any

from .models import (
    DependencyGraph,
    DependencyMetadata,
    ExtensionContext,
    ExtensionDefinition,
    ExtensionLifecycle,
    ExtensionMetadata,
    HookContext,
    HookDefinition,
    HookExecution,
    HookMetadata,
    PluginContext,
    PluginDefinition,
    PluginHealth,
    PluginSession,
    SDKConfiguration,
    SDKContext,
    SDKDefinition,
    SDKMetadata,
    SDKVersion,
)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginDefinition] = {}
        self._lock = RLock()

    def register(self, plugin: PluginDefinition) -> None:
        with self._lock:
            self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> PluginDefinition | None:
        with self._lock:
            return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[PluginDefinition]:
        with self._lock:
            return list(self._plugins.values())

    def discover(self, definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock:
            for definition in definitions:
                plugin_id = definition.get("name") or definition.get("plugin_id")
                if not plugin_id:
                    continue
                self._plugins[plugin_id] = PluginDefinition(
                    plugin_id=plugin_id,
                    name=definition.get("name", plugin_id),
                    version=definition.get("version", "0.1.0"),
                    enabled=True,
                    dependencies=definition.get("dependencies", []),
                    metadata=definition.get("metadata", {}),
                )
            return [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "dependencies": plugin.dependencies,
                    "state": "discovered",
                }
                for plugin in self._plugins.values()
            ]

    def install(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = self.get(plugin_id)
        if plugin is None:
            return None
        return {"name": plugin.name, "version": plugin.version, "state": "installed"}

    def resolve(self, plugin_id: str) -> dict[str, Any] | None:
        plugin = self.get(plugin_id)
        if plugin is None:
            return None
        return {"name": plugin.name, "version": plugin.version, "state": "installed"}


class PluginSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, PluginSession] = {}
        self._lock = RLock()

    def create(self, session_id: str, plugin_id: str) -> PluginSession:
        with self._lock:
            session = PluginSession(session_id=session_id, plugin_id=plugin_id)
            self._sessions[session_id] = session
            return session


class PluginContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, PluginContext] = {}
        self._lock = RLock()

    def create(self, plugin_id: str) -> PluginContext:
        with self._lock:
            context = PluginContext(plugin_id=plugin_id)
            self._contexts[plugin_id] = context
            return context


class PluginConfigurationManager:
    def __init__(self) -> None:
        self._config: dict[str, dict[str, Any]] = {}

    def set(self, plugin_id: str, config: dict[str, Any]) -> None:
        self._config[plugin_id] = config

    def get(self, plugin_id: str) -> dict[str, Any]:
        return dict(self._config.get(plugin_id, {}))


class PluginMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, Any]] = {}

    def set(self, plugin_id: str, metadata: dict[str, Any]) -> None:
        self._metadata[plugin_id] = metadata

    def get(self, plugin_id: str) -> dict[str, Any]:
        return dict(self._metadata.get(plugin_id, {}))


class PluginStatisticsManager:
    def __init__(self) -> None:
        self._stats: dict[str, int] = {"registrations": 0, "enables": 0, "disables": 0}

    def record(self, key: str, value: int = 1) -> None:
        self._stats[key] = self._stats.get(key, 0) + value

    def snapshot(self) -> dict[str, int]:
        return dict(self._stats)


class PluginHealthManager:
    def __init__(self) -> None:
        self._health: dict[str, PluginHealth] = {}

    def mark(self, plugin_id: str, status: str, message: str = "") -> None:
        self._health[plugin_id] = PluginHealth(status=status, message=message)

    def get(self, plugin_id: str) -> PluginHealth | None:
        return self._health.get(plugin_id)


class PluginLifecycleManager:
    def __init__(self) -> None:
        self._states: dict[str, str] = {}

    def set_state(self, plugin_id: str, state: str) -> None:
        self._states[plugin_id] = state

    def get_state(self, plugin_id: str) -> str | None:
        return self._states.get(plugin_id)


class PluginResolver:
    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def resolve(self, plugin_id: str) -> PluginDefinition | None:
        return self._registry.get(plugin_id)


class PluginLoader:
    def __init__(self, resolver: PluginResolver) -> None:
        self._resolver = resolver

    def load(self, plugin_id: str) -> PluginDefinition | None:
        return self._resolver.resolve(plugin_id)


class PluginManager:
    def __init__(self) -> None:
        self.registry = PluginRegistry()
        self.loader = PluginLoader(PluginResolver(self.registry))
        self.lifecycle_manager = PluginLifecycleManager()
        self.session_manager = PluginSessionManager()
        self.context_manager = PluginContextManager()
        self.configuration_manager = PluginConfigurationManager()
        self.metadata_manager = PluginMetadataManager()
        self.statistics_manager = PluginStatisticsManager()
        self.health_manager = PluginHealthManager()

    def register_plugin(self, plugin: Any) -> None:
        plugin_definition = PluginDefinition(
            plugin_id=plugin.plugin_id,
            name=getattr(plugin, "manifest", None).metadata.name if getattr(plugin, "manifest", None) is not None else plugin.plugin_id,
            version=getattr(plugin, "manifest", None).metadata.version if getattr(plugin, "manifest", None) is not None else "0.1.0",
            enabled=True,
            capabilities=[capability for capability in getattr(getattr(plugin, "manifest", None), "metadata_settings", {}).keys()] if getattr(plugin, "manifest", None) is not None else [],
            dependencies=[dependency.dependency_id for dependency in getattr(getattr(plugin, "manifest", None), "dependencies", [])] if getattr(plugin, "manifest", None) is not None else [],
            metadata=getattr(plugin, "manifest", None).metadata.metadata if getattr(plugin, "manifest", None) is not None else {},
        )
        self.registry.register(plugin_definition)
        self.statistics_manager.record("registrations")
        self.lifecycle_manager.set_state(plugin_definition.plugin_id, "registered")
        self.health_manager.mark(plugin_definition.plugin_id, "ready")
        self.metadata_manager.set(plugin_definition.plugin_id, plugin_definition.metadata)

    def list_plugins(self) -> list[PluginDefinition]:
        return self.registry.list_plugins()

    def get_plugin(self, plugin_id: str) -> PluginDefinition | None:
        return self.registry.get(plugin_id)

    def enable_plugin(self, plugin_id: str) -> bool:
        plugin = self.registry.get(plugin_id)
        if plugin is None:
            return False
        self.lifecycle_manager.set_state(plugin_id, "enabled")
        self.statistics_manager.record("enables")
        self.health_manager.mark(plugin_id, "enabled")
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        plugin = self.registry.get(plugin_id)
        if plugin is None:
            return False
        self.lifecycle_manager.set_state(plugin_id, "disabled")
        self.statistics_manager.record("disables")
        self.health_manager.mark(plugin_id, "disabled")
        return True


class ExtensionManager:
    def __init__(self) -> None:
        self._extensions: dict[str, ExtensionDefinition] = {}
        self._lock = RLock()

    def register_extension(self, extension_type: str, extension_id: str, target: str = "core", metadata: dict[str, Any] | None = None) -> ExtensionDefinition:
        with self._lock:
            definition = ExtensionDefinition(extension_id=extension_id, extension_type=extension_type, target=target, metadata=metadata or {})
            self._extensions[extension_id] = definition
            return definition

    def resolve_extension(self, extension_id: str) -> ExtensionDefinition | None:
        with self._lock:
            return self._extensions.get(extension_id)


class SDKManager:
    def __init__(self) -> None:
        self._sdks: dict[str, SDKDefinition] = {}
        self._lock = RLock()

    def register_sdk(self, sdk_id: str, version: str, name: str | None = None, metadata: dict[str, Any] | None = None) -> SDKDefinition:
        with self._lock:
            definition = SDKDefinition(sdk_id=sdk_id, name=name or sdk_id, version=version, metadata=metadata or {})
            self._sdks[sdk_id] = definition
            return definition

    def resolve_sdk(self, sdk_id: str) -> SDKDefinition | None:
        with self._lock:
            return self._sdks.get(sdk_id)


class HookManager:
    def __init__(self) -> None:
        self._hooks: dict[str, list[HookDefinition]] = {}
        self._lock = RLock()

    def register_hook(self, hook_type: str, hook_id: str, target: str = "core", metadata: dict[str, Any] | None = None) -> HookDefinition:
        with self._lock:
            definition = HookDefinition(hook_id=hook_id, hook_type=hook_type, target=target, metadata=metadata or {})
            self._hooks.setdefault(hook_type, []).append(definition)
            return definition

    def execute_hook(self, hook_type: str, context: dict[str, Any]) -> bool:
        with self._lock:
            hooks = self._hooks.get(hook_type, [])
            return bool(hooks) and all(True for _ in hooks)


class DependencyManager:
    def __init__(self) -> None:
        self._dependencies: dict[str, DependencyMetadata] = {}
        self._graph = DependencyGraph()
        self._lock = RLock()

    def register_dependency(self, dependency_id: str, version: str, optional: bool = False, compatibility: list[str] | None = None) -> None:
        with self._lock:
            self._dependencies[dependency_id] = DependencyMetadata(version=version, optional=optional, compatibility=compatibility or [])
            self._graph.nodes.append(dependency_id)

    def resolve_dependency(self, dependency_id: str) -> DependencyMetadata | None:
        with self._lock:
            return self._dependencies.get(dependency_id)

    def graph(self) -> DependencyGraph:
        with self._lock:
            return DependencyGraph(nodes=list(self._graph.nodes), edges=list(self._graph.edges))


class SDKConfigurationManager:
    def __init__(self) -> None:
        self._config: dict[str, SDKConfiguration] = {}

    def set(self, sdk_id: str, config: SDKConfiguration) -> None:
        self._config[sdk_id] = config


class SDKMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, SDKMetadata] = {}

    def set(self, sdk_id: str, metadata: SDKMetadata) -> None:
        self._metadata[sdk_id] = metadata


class SDKRegistry:
    def __init__(self) -> None:
        self._sdks: dict[str, SDKDefinition] = {}

    def register(self, sdk: SDKDefinition) -> None:
        self._sdks[sdk.sdk_id] = sdk

    def get(self, sdk_id: str) -> SDKDefinition | None:
        return self._sdks.get(sdk_id)


class SDKVersionManager:
    def __init__(self) -> None:
        self._versions: dict[str, SDKVersion] = {}

    def set(self, sdk_id: str, version: str) -> None:
        self._versions[sdk_id] = SDKVersion(version=version)

    def get(self, sdk_id: str) -> SDKVersion | None:
        return self._versions.get(sdk_id)


__all__ = [
    "DependencyManager",
    "ExtensionManager",
    "HookManager",
    "PluginConfigurationManager",
    "PluginContextManager",
    "PluginHealthManager",
    "PluginLifecycleManager",
    "PluginManager",
    "PluginMetadataManager",
    "PluginRegistry",
    "PluginResolver",
    "PluginSessionManager",
    "PluginStatisticsManager",
    "SDKConfigurationManager",
    "SDKManager",
    "SDKMetadataManager",
    "SDKRegistry",
    "SDKVersionManager",
]
