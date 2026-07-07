from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List


@dataclass(frozen=True)
class ExtensionContext:
    extension_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtensionSession:
    session_id: str
    extension_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtensionDefinition:
    extension_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtensionManager:
    def __init__(self) -> None:
        self._extensions: Dict[str, ExtensionDefinition] = {}
        self._lock = RLock()

    def register_extension(self, extension_id: str, metadata: dict[str, Any] | None = None) -> ExtensionDefinition:
        with self._lock:
            definition = ExtensionDefinition(extension_id=extension_id, metadata=metadata or {})
            self._extensions[extension_id] = definition
            return definition


class ExtensionRegistry:
    def __init__(self) -> None:
        self._extensions: Dict[str, ExtensionDefinition] = {}
        self._lock = RLock()

    def register(self, extension: ExtensionDefinition) -> None:
        with self._lock:
            self._extensions[extension.extension_id] = extension

    def get(self, extension_id: str) -> ExtensionDefinition | None:
        with self._lock:
            return self._extensions.get(extension_id)


class ExtensionLoader:
    def __init__(self) -> None:
        self._loaded: Dict[str, ExtensionDefinition] = {}
        self._lock = RLock()

    def load(self, extension_id: str, extension: ExtensionDefinition) -> ExtensionDefinition:
        with self._lock:
            self._loaded[extension_id] = extension
            return extension


class ExtensionResolver:
    def __init__(self) -> None:
        self._registry: Dict[str, ExtensionDefinition] = {}
        self._lock = RLock()

    def resolve(self, extension_id: str) -> ExtensionDefinition | None:
        with self._lock:
            return self._registry.get(extension_id)
