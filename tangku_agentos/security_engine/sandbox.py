from __future__ import annotations

from threading import RLock
from uuid import uuid4

from .interfaces import SandboxManager


class SandboxManager(SandboxManager):
    """Sandbox manager abstraction for runtime orchestration."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def create_sandbox(self, name: str, configuration: dict[str, str]) -> str:
        sandbox_id = str(uuid4())
        with self._lock:
            self._sandboxes[sandbox_id] = {"name": name, "configuration": configuration}
        return sandbox_id

    def destroy_sandbox(self, sandbox_id: str) -> None:
        with self._lock:
            self._sandboxes.pop(sandbox_id, None)
