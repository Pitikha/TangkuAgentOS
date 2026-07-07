from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from .models import (
    Deployment,
    DeploymentCluster,
    DeploymentConfiguration,
    DeploymentEnvironment,
    DeploymentFeature,
    DeploymentHealthSummary,
    DeploymentInstance,
    DeploymentLifecycle,
    DeploymentMonitor,
    DeploymentNode,
    DeploymentRollout,
    DeploymentService,
    DeploymentStatus,
    DeploymentTarget,
    DeploymentTargetType,
    DeploymentUpdatePlan,
    RuntimeProfile,
)


class DeploymentEnvironmentType(Enum):
    LOCAL = "local"
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    VM = "vm"
    BARE_METAL = "bare_metal"
    RASPBERRY_PI = "raspberry_pi"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"


class DeploymentProviderInterface(ABC):
    """Contract for a deployment provider adapter."""

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
    def validate_configuration(self, configuration: DeploymentConfiguration) -> bool:
        ...

    @abstractmethod
    def get_environment(self, environment_id: str) -> DeploymentEnvironment:
        ...


class DeploymentManagerInterface(ABC):
    """Orchestrates deployment providers and target environments."""

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
    def get_environment_manager(self) -> "DeploymentEnvironmentManagerInterface":
        ...

    @abstractmethod
    def get_configuration_manager(self) -> "DeploymentConfigurationManagerInterface":
        ...

    @abstractmethod
    def get_service_manager(self) -> "DeploymentServiceManagerInterface":
        ...

    @abstractmethod
    def get_scaling_manager(self) -> "DeploymentScalingManagerInterface":
        ...

    @abstractmethod
    def get_health_manager(self) -> "DeploymentHealthManagerInterface":
        ...

    @abstractmethod
    def get_rollout_manager(self) -> "DeploymentRolloutManagerInterface":
        ...

    @abstractmethod
    def get_update_manager(self) -> "DeploymentUpdateManagerInterface":
        ...

    @abstractmethod
    def get_rollback_manager(self) -> "DeploymentRollbackManagerInterface":
        ...

    @abstractmethod
    def get_monitoring_manager(self) -> "DeploymentMonitoringManagerInterface":
        ...


class DeploymentRegistryInterface(ABC):
    """Stores deployment provider implementations."""

    @abstractmethod
    def register(self, provider_id: str, provider: DeploymentProviderInterface) -> None:
        ...

    @abstractmethod
    def resolve(self, provider_id: str) -> DeploymentProviderInterface:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class DeploymentEnvironmentManagerInterface(ABC):
    """Manages deployment environments and promotion stages."""

    @abstractmethod
    def create_environment(self, environment: DeploymentEnvironment) -> None:
        ...

    @abstractmethod
    def get_environment(self, environment_id: str) -> DeploymentEnvironment:
        ...

    @abstractmethod
    def list_environments(self) -> list[DeploymentEnvironment]:
        ...

    @abstractmethod
    def update_environment(self, environment: DeploymentEnvironment) -> None:
        ...

    @abstractmethod
    def delete_environment(self, environment_id: str) -> None:
        ...

    @abstractmethod
    def resolve_by_stage(self, stage: str) -> DeploymentEnvironment:
        ...


class DeploymentConfigurationManagerInterface(ABC):
    """Manages deployment configuration and secrets injection."""

    @abstractmethod
    def get_configuration(self, deployment_id: str) -> DeploymentConfiguration:
        ...

    @abstractmethod
    def set_configuration(self, deployment_id: str, configuration: DeploymentConfiguration) -> None:
        ...

    @abstractmethod
    def inject_configuration(self, service_id: str, configuration_values: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def inject_secrets(self, deployment_id: str, secrets: dict[str, str]) -> None:
        ...

    @abstractmethod
    def validate_configuration(self, configuration: DeploymentConfiguration) -> bool:
        ...

    @abstractmethod
    def list_configurations(self) -> list[DeploymentConfiguration]:
        ...


class DeploymentServiceManagerInterface(ABC):
    """Manages services, instances, and runtime topology."""

    @abstractmethod
    def register_service(self, service: DeploymentService) -> None:
        ...

    @abstractmethod
    def get_service(self, service_id: str) -> DeploymentService:
        ...

    @abstractmethod
    def list_services(self, deployment_id: str | None = None) -> list[DeploymentService]:
        ...

    @abstractmethod
    def update_service(self, service: DeploymentService) -> None:
        ...

    @abstractmethod
    def remove_service(self, service_id: str) -> None:
        ...

    @abstractmethod
    def list_instances(self, service_id: str) -> list[DeploymentInstance]:
        ...

    @abstractmethod
    def get_instance(self, instance_id: str) -> DeploymentInstance:
        ...


class DeploymentScalingManagerInterface(ABC):
    """Manages scaling and horizontal autoscaling abstraction."""

    @abstractmethod
    def scale_out(self, service_id: str, count: int) -> None:
        ...

    @abstractmethod
    def scale_in(self, service_id: str, count: int) -> None:
        ...

    @abstractmethod
    def set_replica_count(self, service_id: str, replicas: int) -> None:
        ...

    @abstractmethod
    def get_scaling_policy(self, service_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def configure_horizontal_scaling(self, service_id: str, policy: dict[str, Any]) -> None:
        ...


class DeploymentHealthManagerInterface(ABC):
    """Monitors deployment and service health."""

    @abstractmethod
    def check_health(self, target_id: str) -> DeploymentHealthSummary:
        ...

    @abstractmethod
    def register_health_probe(self, service_id: str, probe: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def list_health_probes(self, service_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_health_report(self, deployment_id: str) -> DeploymentHealthSummary:
        ...


class DeploymentRolloutManagerInterface(ABC):
    """Manages rollout strategies and staged releases."""

    @abstractmethod
    def start_rollout(self, deployment_id: str, strategy: str, metadata: dict[str, Any] | None = None) -> DeploymentRollout:
        ...

    @abstractmethod
    def monitor_rollout(self, rollout_id: str) -> DeploymentRollout:
        ...

    @abstractmethod
    def finalize_rollout(self, rollout_id: str) -> None:
        ...

    @abstractmethod
    def abort_rollout(self, rollout_id: str) -> None:
        ...


class DeploymentUpdateManagerInterface(ABC):
    """Manages deployment updates and zero-downtime updates."""

    @abstractmethod
    def plan_update(self, deployment_id: str, update_plan: DeploymentUpdatePlan) -> DeploymentRollout:
        ...

    @abstractmethod
    def apply_update(self, rollout_id: str) -> DeploymentLifecycle:
        ...

    @abstractmethod
    def validate_update(self, rollout_id: str) -> bool:
        ...

    @abstractmethod
    def canary_update(self, deployment_id: str, update_plan: DeploymentUpdatePlan) -> DeploymentRollout:
        ...


class DeploymentRollbackManagerInterface(ABC):
    """Manages rollback operations."""

    @abstractmethod
    def rollback(self, deployment_id: str, rollback_to: str) -> DeploymentLifecycle:
        ...

    @abstractmethod
    def list_rollback_history(self, deployment_id: str) -> list[DeploymentLifecycle]:
        ...


class DeploymentMonitoringManagerInterface(ABC):
    """Integrates observability and monitoring for deployments."""

    @abstractmethod
    def register_monitor(self, monitor: DeploymentMonitor) -> None:
        ...

    @abstractmethod
    def collect_metrics(self, deployment_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def register_alert(self, deployment_id: str, alert_definition: dict[str, Any]) -> str:
        ...

    @abstractmethod
    def list_alerts(self, deployment_id: str) -> list[dict[str, Any]]:
        ...
