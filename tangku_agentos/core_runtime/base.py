from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional


class CoreComponent(ABC):
    """Base interface for core runtime components."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the component."""

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the component for operation."""

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanly stop the component."""

    @abstractmethod
    def status(self) -> Mapping[str, Any]:
        """Return diagnostic status information."""


class Configurable(ABC):
    """Interface for components that support configuration."""

    @abstractmethod
    def configure(self, configuration: Mapping[str, Any]) -> None:
        """Apply configuration settings to the component."""


class Monitorable(ABC):
    """Interface for components that expose runtime health metrics."""

    @abstractmethod
    def metrics(self) -> Mapping[str, Any]:
        """Return runtime metrics for the component."""

    @abstractmethod
    def is_healthy(self) -> bool:
        """Return whether the component is in a healthy state."""
