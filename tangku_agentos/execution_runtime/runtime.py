from __future__ import annotations

from threading import RLock
from typing import Any


class ExecutionManager:
    def __init__(self) -> None:
        self._executions: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def execute(self, execution_id: str, payload: dict[str, Any]) -> str:
        with self._lock:
            self._executions[execution_id] = {"state": "completed", "payload": payload}
            return execution_id

    def get_status(self, execution_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._executions.get(execution_id, {"state": "unknown"}))


class SandboxManager:
    def __init__(self) -> None:
        self._sandboxes: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def create_sandbox(self, sandbox_id: str, metadata: dict[str, Any]) -> str:
        with self._lock:
            self._sandboxes[sandbox_id] = metadata
            return sandbox_id

    def get_status(self, sandbox_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._sandboxes.get(sandbox_id, {}))


class EnvironmentManager:
    def __init__(self) -> None:
        self._environments: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def create_environment(self, environment_id: str, metadata: dict[str, Any]) -> str:
        with self._lock:
            self._environments[environment_id] = metadata
            return environment_id

    def get_status(self, environment_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._environments.get(environment_id, {}))


class ResourceManager:
    def __init__(self) -> None:
        self._reservations: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def reserve(self, execution_id: str, resources: dict[str, Any]) -> None:
        with self._lock:
            self._reservations[execution_id] = resources

    def get_reservation(self, execution_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._reservations.get(execution_id, {}))


class ExecutionQueueManager:
    def __init__(self) -> None:
        self._queue: list[dict[str, Any]] = []
        self._lock = RLock()

    def enqueue(self, execution_id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._queue.append({"execution_id": execution_id, **metadata})

    def peek(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._queue[0]) if self._queue else {}


class ArtifactManager:
    def __init__(self) -> None:
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def store_artifact(self, execution_id: str, artifact: dict[str, Any]) -> None:
        with self._lock:
            self._artifacts[execution_id] = artifact

    def get_artifact(self, execution_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._artifacts.get(execution_id, {}))
