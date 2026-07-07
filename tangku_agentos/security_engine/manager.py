from __future__ import annotations

from .audit import AuditManager
from .authentication import AuthenticationManager
from .authorization import AuthorizationManager
from .interfaces import SecurityManagerInterface
from .permissions import PermissionManager
from .policies import PolicyManager
from .risk import RiskAssessmentManager
from .roles import RoleManager
from .sandbox import SandboxManager
from .secrets import SecretManager
from .trust import TrustManager
from .context import SecurityContextManager
from .session import SecuritySessionManager
from .configuration import SecurityConfigurationManager
from .metadata import SecurityMetadataManager
from .statistics import SecurityStatisticsManager
from .health import SecurityHealthManager


class SecurityManager(SecurityManagerInterface):
    """Central security runtime coordinator."""

    def __init__(self) -> None:
        self._permission_manager = PermissionManager()
        self._role_manager = RoleManager()
        self._policy_manager = PolicyManager()
        self._secret_manager = SecretManager()
        self._audit_manager = AuditManager()
        self._sandbox_manager = SandboxManager()
        self._risk_manager = RiskAssessmentManager()
        self._trust_manager = TrustManager()
        self._authentication_manager = AuthenticationManager()
        self._authorization_manager = AuthorizationManager()
        self._context_manager = SecurityContextManager()
        self._session_manager = SecuritySessionManager()
        self._configuration_manager = SecurityConfigurationManager()
        self._metadata_manager = SecurityMetadataManager()
        self._statistics_manager = SecurityStatisticsManager()
        self._health_manager = SecurityHealthManager()

    def get_permission_manager(self) -> PermissionManager:
        return self._permission_manager

    def get_role_manager(self) -> RoleManager:
        return self._role_manager

    def get_policy_manager(self) -> PolicyManager:
        return self._policy_manager

    def get_secret_manager(self) -> SecretManager:
        return self._secret_manager

    def get_audit_manager(self) -> AuditManager:
        return self._audit_manager

    def get_sandbox_manager(self) -> SandboxManager:
        return self._sandbox_manager

    def get_risk_assessment_manager(self) -> RiskAssessmentManager:
        return self._risk_manager

    def get_trust_manager(self) -> TrustManager:
        return self._trust_manager

    def get_authentication_manager(self) -> AuthenticationManager:
        return self._authentication_manager

    def get_authorization_manager(self) -> AuthorizationManager:
        return self._authorization_manager

    def get_context_manager(self) -> SecurityContextManager:
        return self._context_manager

    def get_session_manager(self) -> SecuritySessionManager:
        return self._session_manager

    def get_configuration_manager(self) -> SecurityConfigurationManager:
        return self._configuration_manager

    def get_metadata_manager(self) -> SecurityMetadataManager:
        return self._metadata_manager

    def get_statistics_manager(self) -> SecurityStatisticsManager:
        return self._statistics_manager

    def get_health_manager(self) -> SecurityHealthManager:
        return self._health_manager
