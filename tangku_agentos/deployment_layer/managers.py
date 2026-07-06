from __future__ import annotations

from abc import ABC, abstractmethod

from .interfaces import (
    DeploymentConfigurationManagerInterface,
    DeploymentEnvironmentManagerInterface,
    DeploymentHealthManagerInterface,
    DeploymentMonitoringManagerInterface,
    DeploymentProviderInterface,
    DeploymentRegistryInterface,
    DeploymentRollbackManagerInterface,
    DeploymentRolloutManagerInterface,
    DeploymentScalingManagerInterface,
    DeploymentServiceManagerInterface,
    DeploymentUpdateManagerInterface,
)
from .models import (
    Deployment,
    DeploymentConfiguration,
    DeploymentEnvironment,
    DeploymentLifecycle,
    DeploymentStatus,
    DeploymentTarget,
)


class DeploymentManager(ABC):
    """Deployment manager architecture."""

    @abstractmethod
    def register_provider(self, provider_id: str, provider: DeploymentProviderInterface) -> None:
        ...

    @abstractmethod
    def resolve_provider(self, provider_id: str) -> DeploymentProviderInterface:
        ...

    @abstractmethod
    def deploy(self, deployment: Deployment) -> DeploymentLifecycle:
        ...

    @abstractmethod
    def terminate(self, deployment_id: str) -> DeploymentStatus:
        ...

    @abstractmethod
    def get_status(self, deployment_id: str) -> DeploymentStatus:
        ...

    @abstractmethod
    def list_providers(self) -> list[str]:
        ...

    @abstractmethod
    def list_targets(self) -> list[DeploymentTarget]:
        ...

    @abstractmethod
    def list_environments(self) -> list[DeploymentEnvironment]:
        ...

    @abstractmethod
    def get_environment_manager(self) -> DeploymentEnvironmentManagerInterface:
        ...

    @abstractmethod
    def get_configuration_manager(self) -> DeploymentConfigurationManagerInterface:
        ...

    @abstractmethod
    def get_service_manager(self) -> DeploymentServiceManagerInterface:
        ...

    @abstractmethod
    def get_scaling_manager(self) -> DeploymentScalingManagerInterface:
        ...

    @abstractmethod
    def get_health_manager(self) -> DeploymentHealthManagerInterface:
        ...

    @abstractmethod
    def get_rollout_manager(self) -> DeploymentRolloutManagerInterface:
        ...

    @abstractmethod
    def get_update_manager(self) -> DeploymentUpdateManagerInterface:
        ...

    @abstractmethod
    def get_rollback_manager(self) -> DeploymentRollbackManagerInterface:
        ...

    @abstractmethod
    def get_monitoring_manager(self) -> DeploymentMonitoringManagerInterface:
        ...
