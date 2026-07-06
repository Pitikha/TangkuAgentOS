from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class PluginState(Enum):
    INSTALLED = 'installed'
    LOADED = 'loaded'
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    FAILED = 'failed'


@dataclass(frozen=True)
class PluginMetadata:
    plugin_id: str
    name: str
    description: str = ''
    version: str = '0.0.1'
    author: str = ''
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginDependency:
    dependency_id: str
    version: str = ''
    optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    metadata: PluginMetadata
    dependencies: List[PluginDependency] = field(default_factory=list)
    entrypoint: str = ''
    permissions: List[str] = field(default_factory=list)
    metadata_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginConfiguration:
    plugin_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginPermission:
    plugin_id: str
    action: str
    allowed: bool = False


@dataclass
class Plugin:
    plugin_id: str
    manifest: PluginManifest
    metadata: PluginMetadata
    state: PluginState = PluginState.INACTIVE
    configuration: PluginConfiguration = field(default_factory=lambda: PluginConfiguration(plugin_id='', settings={}))
