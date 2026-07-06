"""Plugin framework architecture for Tangku AgentOS."""

from .interfaces import (
    PluginInstaller,
    PluginLifecycleManager,
    PluginLoader,
    PluginManagerInterface,
    PluginPackageManager,
    PluginRegistryInterface,
    PluginResolver,
    PluginPermissionManager,
)
from .manager import PluginManager
from .registry import PluginRegistry
from .loader import PluginLoader
from .installer import PluginInstaller
from .resolver import PluginResolver
from .lifecycle import PluginLifecycleManager
from .package_manager import PluginPackageManager
from .permissions import PluginPermissionManager
from .models import (
    Plugin,
    PluginConfiguration,
    PluginDependency,
    PluginManifest,
    PluginMetadata,
    PluginPermission,
    PluginState,
)

__all__ = [
    "PluginManager",
    "PluginRegistry",
    "PluginLoader",
    "PluginResolver",
    "PluginInstaller",
    "PluginPackageManager",
    "PluginLifecycleManager",
    "PluginPermissionManager",
    "Plugin",
    "PluginManifest",
    "PluginMetadata",
    "PluginDependency",
    "PluginConfiguration",
    "PluginPermission",
    "PluginState",
]
