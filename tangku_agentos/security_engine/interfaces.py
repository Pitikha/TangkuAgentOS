from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    Permission,
    Role,
    Policy,
    Credential,
    Secret,
    AuditRecord,
    SecurityEvent,
    RiskLevel,
    SecurityConfiguration,
)


class SecurityManagerInterface(ABC):
    """Interface for security manager."""

    @abstractmethod
    def get_permission_manager(self) -> "PermissionManager":
        ...

    @abstractmethod
    def get_role_manager(self) -> "RoleManager":
        ...

    @abstractmethod
    def get_policy_manager(self) -> "PolicyManager":
        ...

    @abstractmethod
    def get_secret_manager(self) -> "SecretManager":
        ...

    @abstractmethod
    def get_audit_manager(self) -> "AuditManager":
        ...

    @abstractmethod
    def get_sandbox_manager(self) -> "SandboxManager":
        ...

    @abstractmethod
    def get_risk_assessment_manager(self) -> "RiskAssessmentManager":
        ...

    @abstractmethod
    def get_trust_manager(self) -> "TrustManager":
        ...


class PermissionManager(ABC):
    """Interface for permissions."""

    @abstractmethod
    def grant(self, role_id: str, permission: Permission) -> None:
        ...

    @abstractmethod
    def revoke(self, role_id: str, permission_id: str) -> None:
        ...

    @abstractmethod
    def list_permissions(self, role_id: str) -> list[Permission]:
        ...


class RoleManager(ABC):
    """Interface for roles."""

    @abstractmethod
    def create_role(self, role: Role) -> None:
        ...

    @abstractmethod
    def assign_role(self, identity_id: str, role_id: str) -> None:
        ...

    @abstractmethod
    def list_roles(self) -> list[Role]:
        ...


class PolicyManager(ABC):
    """Interface for policies."""

    @abstractmethod
    def create_policy(self, policy: Policy) -> None:
        ...

    @abstractmethod
    def evaluate_policy(self, policy_id: str, context: dict[str, str]) -> bool:
        ...


class AuthenticationManager(ABC):
    """Interface for authentication."""

    @abstractmethod
    def authenticate(self, credentials: Credential) -> bool:
        ...


class AuthorizationManager(ABC):
    """Interface for authorization."""

    @abstractmethod
    def authorize(self, identity_id: str, permission: Permission) -> bool:
        ...


class SecretManager(ABC):
    """Interface for secret storage."""

    @abstractmethod
    def store_secret(self, secret: Secret) -> None:
        ...

    @abstractmethod
    def retrieve_secret(self, secret_id: str) -> Secret:
        ...


class AuditManager(ABC):
    """Interface for audit logging."""

    @abstractmethod
    def record(self, audit_record: AuditRecord) -> None:
        ...

    @abstractmethod
    def query(self, filters: dict[str, str]) -> list[AuditRecord]:
        ...


class SandboxManager(ABC):
    """Interface for sandbox management."""

    @abstractmethod
    def create_sandbox(self, name: str, configuration: dict[str, str]) -> str:
        ...

    @abstractmethod
    def destroy_sandbox(self, sandbox_id: str) -> None:
        ...


class RiskAssessmentManager(ABC):
    """Interface for risk assessment."""

    @abstractmethod
    def assess(self, context: dict[str, str]) -> RiskLevel:
        ...


class TrustManager(ABC):
    """Interface for trust management."""

    @abstractmethod
    def evaluate_trust(self, identity_id: str) -> bool:
        ...
