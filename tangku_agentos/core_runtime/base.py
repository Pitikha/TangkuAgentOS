from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional


class CoreComponent(ABC):
    """
    Base interface for all core runtime components.

    This abstract class defines the common interface for all components
    in the TangkuAgentOS core runtime, including initialization,
    shutdown, and status reporting.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique name of the component.

        Returns:
            str: The name of the component.
        """

    @abstractmethod
    def initialize(self) -> None:
        """
        Prepare the component for operation.

        This method should be called before the component is used.
        It performs any necessary setup or initialization.
        """

    @abstractmethod
    def shutdown(self) -> None:
        """
        Cleanly stop the component.

        This method should be called when the component is no longer needed.
        It performs any necessary cleanup or teardown.
        """

    @abstractmethod
    def status(self) -> Mapping[str, Any]:
        """
        Return diagnostic status information for the component.

        Returns:
            Mapping[str, Any]: A dictionary containing status information.
        """


class Configurable(ABC):
    """
    Interface for components that support configuration.

    This abstract class defines the interface for components that can be
    configured with a dictionary of settings.
    """

    @abstractmethod
    def configure(self, configuration: Mapping[str, Any]) -> None:
        """
        Apply configuration settings to the component.

        Args:
            configuration (Mapping[str, Any]): A dictionary of configuration settings.
        """


class Monitorable(ABC):
    """
    Interface for components that expose runtime health metrics.

    This abstract class defines the interface for components that can report
    their health status and runtime metrics.
    """

    @abstractmethod
    def metrics(self) -> Mapping[str, Any]:
        """
        Return runtime metrics for the component.

        Returns:
            Mapping[str, Any]: A dictionary containing runtime metrics.
        """

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if the component is in a healthy state.

        Returns:
            bool: True if the component is healthy, False otherwise.
        """


class HealthCheckable(ABC):
    """
    Interface for components that support health checks.

    This abstract class extends Monitorable to include explicit health check
    functionality, which can be used for periodic health monitoring.
    """

    @abstractmethod
    def check_health(self) -> bool:
        """
        Perform a health check on the component.

        Returns:
            bool: True if the component is healthy, False otherwise.
        """

    @abstractmethod
    def health_report(self) -> Mapping[str, Any]:
        """
        Generate a detailed health report for the component.

        Returns:
            Mapping[str, Any]: A dictionary containing health status and details.
        """
