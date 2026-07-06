from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PluginState(str, Enum):
    INSTALLED = "installed"
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"


@dataclass(slots=True)
class PluginDefinition:
    plugin_id: str
    name: str
    version: str = "0.1.0"
    enabled: bool = True
    capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PluginContext:
    plugin_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PluginSession:
    session_id: str
    plugin_id: str
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PluginHealth:
    status: str = "ready"
    message: str = ""
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class ExtensionDefinition:
    extension_id: str
    extension_type: str
    target: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtensionContext:
    extension_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtensionLifecycle:
    state: str = "registered"


@dataclass(slots=True)
class ExtensionMetadata:
    version: str = "0.1.0"
    capabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SDKDefinition:
    sdk_id: str
    name: str
    version: str = "0.1.0"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SDKContext:
    sdk_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SDKConfiguration:
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SDKMetadata:
    description: str = ""
    capabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SDKVersion:
    version: str = "0.1.0"


@dataclass(slots=True)
class HookDefinition:
    hook_id: str
    hook_type: str
    target: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HookContext:
    event: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HookExecution:
    executed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HookMetadata:
    description: str = ""


@dataclass(slots=True)
class DependencyMetadata:
    version: str = "0.1.0"
    optional: bool = False
    compatibility: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DependencyGraph:
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)


__all__ = [
    "DependencyGraph",
    "DependencyMetadata",
    "ExtensionContext",
    "ExtensionDefinition",
    "ExtensionLifecycle",
    "ExtensionMetadata",
    "HookContext",
    "HookDefinition",
    "HookExecution",
    "HookMetadata",
    "PluginContext",
    "PluginDefinition",
    "PluginHealth",
    "PluginSession",
    "SDKConfiguration",
    "SDKContext",
    "SDKDefinition",
    "SDKMetadata",
    "SDKVersion",
]
