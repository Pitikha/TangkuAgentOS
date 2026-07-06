from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class DeploymentTargetType(Enum):
    LOCAL = "local"
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    VM = "vm"
    BARE_METAL = "bare_metal"
    RASPBERRY_PI = "raspberry_pi"
    HOME_SERVER = "home_server"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"


class DeploymentStage(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DeploymentTarget:
    target_id: str
    target_type: DeploymentTargetType
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeProfile:
    profile_id: str
    name: str
    description: str = ""
    environment_variables: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentInstance:
    instance_id: str
    service_id: str
    node_id: str
    container_id: Optional[str]
    status: DeploymentStatus
    runtime_profile: RuntimeProfile
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentNode:
    node_id: str
    cluster_id: str
    hostname: str
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentContainer:
    container_id: str
    image: str
    name: str
    runtime_profile: RuntimeProfile
    status: DeploymentStatus
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentService:
    service_id: str
    name: str
    version: str
    containers: List[DeploymentContainer] = field(default_factory=list)
    instances: List[DeploymentInstance] = field(default_factory=list)
    runtime_profile: RuntimeProfile = field(default_factory=lambda: RuntimeProfile("default", "default"))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentCluster:
    cluster_id: str
    name: str
    nodes: List[DeploymentNode] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentEnvironment:
    environment_id: str
    name: str
    stage: DeploymentStage
    description: str = ''
    supported_targets: List[DeploymentTargetType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentConfiguration:
    deployment_id: str
    target: DeploymentTarget
    services: List[DeploymentService] = field(default_factory=list)
    runtime_profile: RuntimeProfile = field(default_factory=lambda: RuntimeProfile("default", "default"))
    secrets: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Deployment:
    deployment_id: str
    name: str
    environment: DeploymentEnvironment
    target: DeploymentTarget
    configuration: DeploymentConfiguration
    services: List[DeploymentService] = field(default_factory=list)
    cluster: Optional[DeploymentCluster] = None
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentLifecycle:
    lifecycle_id: str
    deployment_id: str
    status: DeploymentStatus
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentRollout:
    rollout_id: str
    deployment_id: str
    strategy: str
    progress: float = 0.0
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentUpdatePlan:
    plan_id: str
    deployment_id: str
    changes: Dict[str, Any] = field(default_factory=dict)
    strategy: str = "rolling"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentMonitor:
    monitor_id: str
    deployment_id: str
    name: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentHealthSummary:
    deployment_id: str
    status: HealthStatus
    healthy_instances: int = 0
    unhealthy_instances: int = 0
    degraded_instances: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeploymentFeature:
    feature_id: str
    name: str
    description: str = ''
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
