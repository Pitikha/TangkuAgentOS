from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List


@dataclass(frozen=True)
class SDKContext:
    context_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKConfiguration:
    configuration_id: str
    language: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKMetadata:
    sdk_id: str
    name: str
    version: str = "0.1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKSession:
    session_id: str
    sdk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeveloperSDKManager:
    def __init__(self) -> None:
        self._sdks: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def register_sdk(self, sdk_id: str, context: SDKContext, configuration: SDKConfiguration, metadata: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._sdks[sdk_id] = {"context": context, "configuration": configuration, "metadata": metadata or {}}

    def get_sdk(self, sdk_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._sdks.get(sdk_id)


class SDKRegistry:
    def __init__(self) -> None:
        self._registrations: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def register(self, sdk_id: str, metadata: SDKMetadata, configuration: SDKConfiguration | None = None) -> None:
        with self._lock:
            self._registrations[sdk_id] = {"metadata": metadata, "configuration": configuration}

    def resolve(self, sdk_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._registrations.get(sdk_id)
