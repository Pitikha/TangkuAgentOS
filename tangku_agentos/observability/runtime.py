from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class ObservabilityContext:
    context_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservabilitySession:
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservabilityComponent:
    component_id: str
    component_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ObservabilityRegistry:
    def __init__(self) -> None:
        self._components: dict[str, ObservabilityComponent] = {}
        self._lock = RLock()

    def register(self, component: ObservabilityComponent) -> None:
        with self._lock:
            self._components[component.component_id] = component

    def get(self, component_id: str) -> ObservabilityComponent | None:
        with self._lock:
            return self._components.get(component_id)


class ObservabilitySessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, ObservabilitySession] = {}
        self._lock = RLock()

    def create(self, session_id: str, metadata: dict[str, Any] | None = None) -> ObservabilitySession:
        with self._lock:
            session = ObservabilitySession(session_id=session_id, metadata=metadata or {})
            self._sessions[session_id] = session
            return session


class ObservabilityContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, ObservabilityContext] = {}
        self._lock = RLock()

    def create(self, context_id: str, metadata: dict[str, Any] | None = None) -> ObservabilityContext:
        with self._lock:
            context = ObservabilityContext(context_id=context_id, metadata=metadata or {})
            self._contexts[context_id] = context
            return context


class ObservabilityLifecycleManager:
    def __init__(self) -> None:
        self._states: dict[str, str] = {}
        self._lock = RLock()

    def set_state(self, component_id: str, state: str) -> None:
        with self._lock:
            self._states[component_id] = state

    def get_state(self, component_id: str) -> str | None:
        with self._lock:
            return self._states.get(component_id)


class ObservabilityConfigurationManager:
    def __init__(self) -> None:
        self._config: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, component_id: str, config: dict[str, Any]) -> None:
        with self._lock:
            self._config[component_id] = dict(config)

    def get(self, component_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._config.get(component_id, {}))


class ObservabilityMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, component_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._metadata[component_id] = dict(metadata)

    def get(self, component_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._metadata.get(component_id, {}))


class ObservabilityStatisticsManager:
    def __init__(self) -> None:
        self._stats: dict[str, int] = {"events": 0, "snapshots": 0}
        self._lock = RLock()

    def record(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._stats[name] = self._stats.get(name, 0) + value

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stats)


class ObservabilityHealthManager:
    def __init__(self) -> None:
        self._health: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def set(self, component_id: str, status: str, details: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._health[component_id] = {"status": status, **(details or {})}

    def get(self, component_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._health.get(component_id)
