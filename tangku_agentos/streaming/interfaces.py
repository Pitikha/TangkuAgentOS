from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TokenStream(ABC):
    """Interface for token streaming."""

    @abstractmethod
    def on_token(self, token: str) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...


class EventStream(ABC):
    """Interface for streaming events."""

    @abstractmethod
    def on_event(self, event: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...


class PartialResultStream(ABC):
    """Interface for partial execution results."""

    @abstractmethod
    def on_partial(self, result: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...


class ProgressStream(ABC):
    """Interface for progress updates."""

    @abstractmethod
    def on_progress(self, percent: float, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...


class ArtifactStream(ABC):
    """Interface for artifact streaming."""

    @abstractmethod
    def on_artifact(self, artifact: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...
