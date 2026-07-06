from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RiskLevel(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass(frozen=True)
class Permission:
    permission_id: str
    name: str
    description: str = ''
    resource: str = ''
    actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Role:
    role_id: str
    name: str
    description: str = ''
    permissions: List[Permission] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    policy_id: str
    name: str
    rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Credential:
    credential_id: str
    identity: str
    secret: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Secret:
    secret_id: str
    name: str
    value: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    event: str
    identity: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityEvent:
    event_id: str
    event_type: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityConfiguration:
    settings: Dict[str, Any] = field(default_factory=dict)
    policies: List[Policy] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityContext:
    context_id: str
    subject_id: str
    resource: str
    action: str
    source: str = "runtime"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecuritySession:
    session_id: str
    subject_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityMetadata:
    resource_id: str
    owner: str = "system"
    classification: str = "internal"
    metadata: Dict[str, Any] = field(default_factory=dict)
