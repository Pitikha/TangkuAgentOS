from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Plugin, PluginConfiguration, PluginDependency, PluginManifest, PluginPermission, PluginState


class PluginManagerInterface(ABC):
    """Interface for plugin management."""

    @abstractmethod
    def register_plugin(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def get_plugin(self, plugin_id: str) -> Plugin:
        ...

    @abstractmethod
    def list_plugins(self) -> list[Plugin]:
        ...

    @abstractmethod
    def uninstall_plugin(self, plugin_id: str) -> None:
        ...


class PluginRegistryInterface(ABC):
    """Interface for plugin registry."""

    @abstractmethod
    def register(self, plugin: Plugin) -> None:
        ...

    @abstractmethod
    def resolve(self, plugin_id: str) -> Plugin:
        ...


class PluginLoader(ABC):
    """Interface for plugin loading."""

    @abstractmethod
    def load(self, manifest: PluginManifest) -> Plugin:
        ...


class PluginResolver(ABC):
    """Interface for plugin resolution."""

    @abstractmethod
    def resolve(self, plugin_id: str) -> Plugin:
        ...


class PluginInstaller(ABC):
    """Interface for plugin installation."""

    @abstractmethod
    def install(self, plugin: Plugin) -> None:
        ...


class PluginPackageManager(ABC):
    """Interface for plugin package management."""

    @abstractmethod
    def package(self, plugin: Plugin) -> str:
        ...

    @abstractmethod
    def install_package(self, package_path: str) -> Plugin:
        ...


class PluginLifecycleManager(ABC):
    """Interface for plugin lifecycle management."""

    @abstractmethod
    def activate(self, plugin_id: str) -> None:
        ...

    @abstractmethod
    def deactivate(self, plugin_id: str) -> None:
        ...


class PluginPermissionManager(ABC):
    """Interface for plugin permissions."""

    @abstractmethod
    def authorize(self, plugin_id: str, action: str) -> bool:
        ...
