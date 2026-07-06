from __future__ import annotations

from .interfaces import MemoryBackend


class MemoryBackendImpl(MemoryBackend):
    """Simple in-process backend implementation for memory persistence hooks."""

    def __init__(self) -> None:
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected
