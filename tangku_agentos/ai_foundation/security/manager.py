"""
AI Foundation Framework - Security Manager

This module provides the SecurityManager class for managing security in the AI Foundation.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels."""
    DENIED = auto()
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ADMIN = auto()


class AuthMethod(Enum):
    """Authentication methods."""
    API_KEY = auto()
    JWT = auto()
    OAUTH = auto()
    BASIC = auto()
    CUSTOM = auto()


@dataclass
class User:
    """Represents a user in the AI Foundation."""
    user_id: str
    username: str
    email: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)
    api_keys: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def add_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def remove_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def add_role(self, role: str) -> None:
        self.roles.add(role)

    def remove_role(self, role: str) -> None:
        self.roles.discard(role)

    def add_api_key(self, api_key: str) -> None:
        self.api_keys.add(api_key)

    def remove_api_key(self, api_key: str) -> None:
        self.api_keys.discard(api_key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "permissions": list(self.permissions),
            "roles": list(self.roles),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            email=data.get("email"),
            permissions=set(data.get("permissions", [])),
            roles=set(data.get("roles", [])),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.utcnow().isoformat())),
            metadata=data.get("metadata", {}),
        )


@dataclass
class APIKey:
    """Represents an API key."""
    key_id: str
    key_hash: str
    user_id: str
    permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def verify(self, key: str) -> bool:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return hmac.compare_digest(key_hash, self.key_hash)

    def use(self) -> None:
        self.last_used = datetime.utcnow()
        self.usage_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "user_id": self.user_id,
            "permissions": list(self.permissions),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "metadata": self.metadata,
        }

    @classmethod
    def generate(cls, user_id: str, permissions: Set[str] = None, expires_at: Optional[datetime] = None) -> "APIKey":
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_id = f"apikey_{secrets.token_urlsafe(16)}"
        return cls(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            permissions=permissions or set(),
            expires_at=expires_at,
        )


@dataclass
class SecurityManagerMetrics:
    """Metrics for the security manager."""
    auth_attempts: int = 0
    auth_successes: int = 0
    auth_failures: int = 0
    permission_checks: int = 0
    permission_granted: int = 0
    permission_denied: int = 0
    api_key_operations: int = 0
    user_operations: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auth_attempts": self.auth_attempts,
            "auth_successes": self.auth_successes,
            "auth_failures": self.auth_failures,
            "permission_checks": self.permission_checks,
            "permission_granted": self.permission_granted,
            "permission_denied": self.permission_denied,
            "api_key_operations": self.api_key_operations,
            "user_operations": self.user_operations,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class SecurityManager:
    """
    Manager for security in the AI Foundation.
    
    This class provides comprehensive security management including
    authentication, authorization, API key management, and audit logging.
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        self._config = config
        self._foundation = foundation
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, APIKey] = {}
        self._key_lookup: Dict[str, str] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._metrics = SecurityManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        logger.info("SecurityManager initialized")

    @property
    def config(self) -> "AIConfig":
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        return self._foundation

    @property
    def metrics(self) -> SecurityManagerMetrics:
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def is_started(self) -> bool:
        return self._started

    async def initialize(self) -> None:
        if self._initialized:
            logger.warning("SecurityManager already initialized")
            return
        logger.info("Initializing SecurityManager...")
        await self._load_default_users()
        self._initialized = True
        logger.info("SecurityManager initialized successfully")

    async def start(self) -> None:
        if self._started:
            logger.warning("SecurityManager already started")
            return
        if not self._initialized:
            await self.initialize()
        logger.info("Starting SecurityManager...")
        self._started = True
        logger.info("SecurityManager started successfully")

    async def stop(self) -> None:
        if not self._started:
            logger.warning("SecurityManager not started")
            return
        logger.info("Stopping SecurityManager...")
        self._started = False
        logger.info("SecurityManager stopped successfully")

    async def _load_default_users(self) -> None:
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@tangkuagentos.ai",
            permissions={"admin", "read", "write", "execute", "manage"},
            roles={"admin"},
        )
        await self.create_user(admin_user)
        
        system_user = User(
            user_id="system",
            username="system",
            permissions={"read", "write", "execute"},
            roles={"system"},
        )
        await self.create_user(system_user)

    async def create_user(self, user: User) -> str:
        async with self._lock:
            if user.user_id in self._users:
                raise ValueError(f"User with ID {user.user_id} already exists")
            self._users[user.user_id] = user
            self._metrics.user_operations += 1
            await self._log_audit(action="create_user", user_id=user.user_id, success=True, details={"username": user.username, "email": user.email})
            logger.debug(f"User created: {user.user_id}")
            return user.user_id

    async def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def list_users(self) -> List[User]:
        return list(self._users.values())

    async def update_user(self, user_id: str, **kwargs) -> bool:
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self._metrics.user_operations += 1
            await self._log_audit(action="update_user", user_id=user_id, success=True, details=kwargs)
            return True

    async def delete_user(self, user_id: str) -> bool:
        async with self._lock:
            if user_id not in self._users:
                return False
            user = self._users[user_id]
            api_key_ids = [key_id for key_id, key in self._api_keys.items() if key.user_id == user_id]
            for key_id in api_key_ids:
                del self._api_keys[key_id]
                if key_id in self._key_lookup:
                    del self._key_lookup[self._api_keys[key_id].key_hash]
            del self._users[user_id]
            self._metrics.user_operations += 1
            await self._log_audit(action="delete_user", user_id=user_id, success=True, details={"username": user.username})
            return True

    async def generate_api_key(self, user_id: str, permissions: Optional[Set[str]] = None, expires_at: Optional[datetime] = None) -> Optional[APIKey]:
        user = await self.get_user(user_id)
        if not user:
            return None
        async with self._lock:
            if permissions is None:
                permissions = user.permissions
            api_key = APIKey.generate(user_id, permissions, expires_at)
            self._api_keys[api_key.key_id] = api_key
            self._key_lookup[api_key.key_hash] = api_key.key_id
            user.add_api_key(api_key.key_id)
            self._metrics.api_key_operations += 1
            await self._log_audit(action="generate_api_key", user_id=user_id, success=True, details={"key_id": api_key.key_id, "permissions": list(permissions)})
            logger.debug(f"API key generated: {api_key.key_id}")
            return api_key

    async def get_api_key(self, key_id: str) -> Optional[APIKey]:
        return self._api_keys.get(key_id)

    async def get_api_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        key_id = self._key_lookup.get(key_hash)
        if key_id:
            return self._api_keys.get(key_id)
        return None

    async def list_api_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        if user_id:
            return [key for key in self._api_keys.values() if key.user_id == user_id]
        return list(self._api_keys.values())

    async def revoke_api_key(self, key_id: str) -> bool:
        async with self._lock:
            api_key = self._api_keys.get(key_id)
            if not api_key:
                return False
            user = await self.get_user(api_key.user_id)
            if user:
                user.remove_api_key(key_id)
            if api_key.key_hash in self._key_lookup:
                del self._key_lookup[api_key.key_hash]
            del self._api_keys[key_id]
            self._metrics.api_key_operations += 1
            await self._log_audit(action="revoke_api_key", user_id=api_key.user_id, success=True, details={"key_id": key_id})
            return True

    async def authenticate_api_key(self, key: str) -> Optional[User]:
        self._metrics.auth_attempts += 1
        import hashlib
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        api_key = await self.get_api_key_by_hash(key_hash)
        if not api_key:
            self._metrics.auth_failures += 1
            await self._log_audit(action="authenticate", success=False, details={"error": "Invalid API key"})
            return None
        if api_key.is_expired:
            self._metrics.auth_failures += 1
            await self._log_audit(action="authenticate", user_id=api_key.user_id, success=False, details={"error": "API key expired"})
            return None
        user = await self.get_user(api_key.user_id)
        if not user:
            self._metrics.auth_failures += 1
            await self._log_audit(action="authenticate", success=False, details={"error": "User not found"})
            return None
        api_key.use()
        self._metrics.auth_successes += 1
        await self._log_audit(action="authenticate", user_id=user.user_id, success=True, details={"key_id": api_key.key_id})
        return user

    async def check_permission(self, user_id: str, permission: str) -> bool:
        self._metrics.permission_checks += 1
        user = await self.get_user(user_id)
        if not user:
            self._metrics.permission_denied += 1
            await self._log_audit(action="check_permission", user_id=user_id, success=False, details={"permission": permission, "error": "User not found"})
            return False
        has_permission = user.has_permission(permission)
        if has_permission:
            self._metrics.permission_granted += 1
        else:
            self._metrics.permission_denied += 1
        await self._log_audit(action="check_permission", user_id=user_id, success=has_permission, details={"permission": permission})
        return has_permission

    async def check_role(self, user_id: str, role: str) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        return user.has_role(role)

    async def get_permissions(self, user_id: str) -> Set[str]:
        user = await self.get_user(user_id)
        if not user:
            return set()
        return user.permissions

    async def get_roles(self, user_id: str) -> Set[str]:
        user = await self.get_user(user_id)
        if not user:
            return set()
        return user.roles

    async def _log_audit(self, action: str, user_id: Optional[str] = None, success: bool = True, details: Optional[Dict[str, Any]] = None) -> None:
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "success": success,
            "details": details or {},
        }
        self._audit_log.append(audit_entry)
        if success:
            logger.info(f"AUDIT: {action} by {user_id or 'unknown'}", extra=details)
        else:
            logger.warning(f"AUDIT: {action} by {user_id or 'unknown'} FAILED", extra=details)

    async def get_audit_log(self, user_id: Optional[str] = None, action: Optional[str] = None, success: Optional[bool] = None, limit: Optional[int] = None, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logs = self._audit_log.copy()
        if user_id:
            logs = [log for log in logs if log.get("user_id") == user_id]
        if action:
            logs = [log for log in logs if log.get("action") == action]
        if success is not None:
            logs = [log for log in logs if log.get("success") == success]
        if since:
            logs = [log for log in logs if datetime.fromisoformat(log.get("timestamp", "")) >= since]
        if limit:
            logs = logs[-limit:]
        return logs

    async def get_info(self) -> Dict[str, Any]:
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "users": len(self._users),
            "api_keys": len(self._api_keys),
            "audit_log_entries": len(self._audit_log),
            "metrics": self._metrics.to_dict(),
            "config": {
                "api_key_isolation": self._config.security.api_key_isolation,
                "encrypted_secrets": self._config.security.encrypted_secrets,
                "require_authentication": self._config.security.require_authentication,
                "permission_validation": self._config.security.permission_validation,
                "auth_backend": self._config.security.auth_backend,
                "audit_logging_enabled": self._config.security.audit_logging_enabled,
                "audit_log_retention": self._config.security.audit_log_retention,
            }
        }

    async def reset(self) -> None:
        logger.info("Resetting SecurityManager...")
        async with self._lock:
            self._users.clear()
            self._api_keys.clear()
            self._key_lookup.clear()
            self._audit_log.clear()
            self._metrics = SecurityManagerMetrics()
            self._initialized = False
            self._started = False
        logger.info("SecurityManager reset successfully")

    def __repr__(self) -> str:
        return f"SecurityManager(initialized={self._initialized}, started={self._started}, users={len(self._users)})"
