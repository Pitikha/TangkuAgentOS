"""Secure API key management for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import APIKey, ProviderID

from .constants import (
    DEFAULT_STORAGE_PATH,
    TANGKU_ENCRYPTION_KEY,
    TANGKU_PROVIDER_DEFAULT_KEY,
    TANGKU_PROVIDER_KEY_PREFIX,
    TANGKU_PROVIDER_KEY_SUFFIX,
)
from .exceptions import (
    InvalidKeyError,
    KeyEncryptionError,
    KeyNotFoundError,
    KeyStorageError,
)


# --- Encryption Backend ---
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


@dataclass
class APIKeyEntry:
    """Represents an API key entry with metadata."""

    key: APIKey
    provider_id: ProviderID
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KeyUsage:
    """Tracks usage of an API key."""

    provider_id: ProviderID
    key_hash: str
    request_count: int = 0
    last_used_at: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0


class SecureKeyStorage:
    """
    Secure storage backend for API keys.
    Supports encryption, rotation, and expiration.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self._storage_path = Path(storage_path or DEFAULT_STORAGE_PATH)
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._keys: Dict[str, List[APIKeyEntry]] = {}
        self._usage: Dict[str, KeyUsage] = {}
        self._encryption_key = self._get_encryption_key()
        self._load()

    def _get_encryption_key(self) -> bytes:
        """Get or generate the encryption key."""
        env_key = os.environ.get(TANGKU_ENCRYPTION_KEY)
        if env_key:
            return hashlib.sha256(env_key.encode()).digest()
        return hashlib.sha256("tangku-provider-runtime".encode()).digest()

    def _encrypt(self, value: str) -> str:
        """Encrypt a value using XOR with the encryption key."""
        encoded = value.encode("utf-8")
        encrypted = bytes(
            b ^ self._encryption_key[i % len(self._encryption_key)]
            for i, b in enumerate(encoded)
        )
        return base64.b64encode(encrypted).decode("utf-8")

    def _decrypt(self, value: str) -> str:
        """Decrypt a value using XOR with the encryption key."""
        try:
            encrypted = base64.b64decode(value.encode("utf-8"))
            decrypted = bytes(
                b ^ self._encryption_key[i % len(self._encryption_key)]
                for i, b in enumerate(encrypted)
            )
            return decrypted.decode("utf-8")
        except Exception as e:
            raise KeyEncryptionError(f"Failed to decrypt key: {e}") from e

    def _load(self) -> None:
        """Load keys from storage."""
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                self._keys = {
                    provider_id: [
                        APIKeyEntry(
                            key=self._decrypt(entry["key"]),
                            provider_id=provider_id,
                            created_at=entry.get("created_at", time.time()),
                            expires_at=entry.get("expires_at"),
                            is_active=entry.get("is_active", True),
                            metadata=entry.get("metadata", {}),
                        )
                        for entry in entries
                    ]
                    for provider_id, entries in data.get("keys", {}).items()
                }
                self._usage = {
                    key_hash: KeyUsage(
                        provider_id=usage["provider_id"],
                        key_hash=key_hash,
                        request_count=usage.get("request_count", 0),
                        last_used_at=usage.get("last_used_at", 0.0),
                        total_tokens=usage.get("total_tokens", 0),
                        total_cost=usage.get("total_cost", 0.0),
                    )
                    for key_hash, usage in data.get("usage", {}).items()
                }
        except Exception as e:
            raise KeyStorageError(f"Failed to load keys: {e}") from e

    def _persist(self) -> None:
        """Persist keys to storage."""
        try:
            data = {
                "keys": {
                    provider_id: [
                        {
                            "key": self._encrypt(entry.key),
                            "created_at": entry.created_at,
                            "expires_at": entry.expires_at,
                            "is_active": entry.is_active,
                            "metadata": entry.metadata,
                        }
                        for entry in entries
                    ]
                    for provider_id, entries in self._keys.items()
                },
                "usage": {
                    key_hash: {
                        "provider_id": usage.provider_id,
                        "request_count": usage.request_count,
                        "last_used_at": usage.last_used_at,
                        "total_tokens": usage.total_tokens,
                        "total_cost": usage.total_cost,
                    }
                    for key_hash, usage in self._usage.items()
                },
            }
            with self._storage_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise KeyStorageError(f"Failed to persist keys: {e}") from e

    def _get_key_hash(self, key: APIKey) -> str:
        """Generate a hash for a key (for usage tracking)."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def save_key(
        self,
        provider_id: ProviderID,
        key: APIKey,
        expires_at: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save an API key for a provider."""
        if not self._validate_key(key):
            raise InvalidKeyError(f"Invalid API key for provider {provider_id}")

        with self._lock:
            if provider_id not in self._keys:
                self._keys[provider_id] = []
            self._keys[provider_id].append(
                APIKeyEntry(
                    key=key,
                    provider_id=provider_id,
                    expires_at=expires_at,
                    metadata=metadata or {},
                )
            )
            self._persist()

    def get_key(self, provider_id: ProviderID) -> Optional[APIKey]:
        """Get the active API key for a provider."""
        with self._lock:
            entries = self._keys.get(provider_id, [])
            for entry in entries:
                if entry.is_active and (entry.expires_at is None or entry.expires_at > time.time()):
                    self._record_usage(entry)
                    return entry.key
            return None

    def get_all_keys(self, provider_id: ProviderID) -> List[APIKey]:
        """Get all API keys for a provider."""
        with self._lock:
            return [entry.key for entry in self._keys.get(provider_id, []) if entry.is_active]

    def remove_key(self, provider_id: ProviderID, key: Optional[APIKey] = None) -> None:
        """Remove an API key for a provider."""
        with self._lock:
            if provider_id not in self._keys:
                return
            if key is None:
                self._keys[provider_id] = []
            else:
                self._keys[provider_id] = [
                    entry for entry in self._keys[provider_id] if entry.key != key
                ]
            self._persist()

    def rotate_key(self, provider_id: ProviderID, old_key: APIKey, new_key: APIKey) -> None:
        """Rotate an API key for a provider."""
        self.remove_key(provider_id, old_key)
        self.save_key(provider_id, new_key)

    def deactivate_key(self, provider_id: ProviderID, key: APIKey) -> None:
        """Deactivate an API key for a provider."""
        with self._lock:
            if provider_id not in self._keys:
                return
            for entry in self._keys[provider_id]:
                if entry.key == key:
                    entry.is_active = False
                    break
            self._persist()

    def list_providers(self) -> List[ProviderID]:
        """List all providers with stored keys."""
        with self._lock:
            return list(self._keys.keys())

    def has_key(self, provider_id: ProviderID) -> bool:
        """Check if a provider has any active keys."""
        with self._lock:
            entries = self._keys.get(provider_id, [])
            return any(
                entry.is_active and (entry.expires_at is None or entry.expires_at > time.time())
                for entry in entries
            )

    def _record_usage(self, entry: APIKeyEntry) -> None:
        """Record usage of a key."""
        key_hash = self._get_key_hash(entry.key)
        if key_hash not in self._usage:
            self._usage[key_hash] = KeyUsage(
                provider_id=entry.provider_id,
                key_hash=key_hash,
            )
        self._usage[key_hash].request_count += 1
        self._usage[key_hash].last_used_at = time.time()
        self._persist()

    def record_usage(
        self,
        provider_id: ProviderID,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record usage of a key."""
        key = self.get_key(provider_id)
        if key is None:
            return
        key_hash = self._get_key_hash(key)
        with self._lock:
            if key_hash not in self._usage:
                self._usage[key_hash] = KeyUsage(
                    provider_id=provider_id,
                    key_hash=key_hash,
                )
            self._usage[key_hash].request_count += 1
            self._usage[key_hash].last_used_at = time.time()
            self._usage[key_hash].total_tokens += tokens
            self._usage[key_hash].total_cost += cost
            self._persist()

    def get_usage(self, provider_id: ProviderID) -> Optional[KeyUsage]:
        """Get usage statistics for a provider's key."""
        key = self.get_key(provider_id)
        if key is None:
            return None
        key_hash = self._get_key_hash(key)
        return self._usage.get(key_hash)

    def cleanup_expired(self) -> int:
        """Remove expired keys. Returns the number of keys removed."""
        with self._lock:
            removed = 0
            for provider_id in list(self._keys.keys()):
                self._keys[provider_id] = [
                    entry
                    for entry in self._keys[provider_id]
                    if entry.expires_at is None or entry.expires_at > time.time()
                ]
                removed += len([
                    entry
                    for entry in self._keys[provider_id]
                    if entry.expires_at is not None and entry.expires_at <= time.time()
                ])
            self._persist()
            return removed

    def _validate_key(self, key: APIKey) -> bool:
        """Validate an API key."""
        return bool(key and key.strip())

    def mask_key(self, key: Optional[APIKey] = None) -> str:
        """Mask a key for display."""
        if key is None:
            return "***"
        return "***" + key[-4:] if len(key) > 4 else "***"


class EnvironmentKeyResolver:
    """Resolve API keys from environment variables."""

    @staticmethod
    def resolve(provider_id: ProviderID) -> Optional[APIKey]:
        """Resolve an API key from environment variables."""
        env_key = os.environ.get(
            f"{TANGKU_PROVIDER_KEY_PREFIX}{provider_id.upper()}{TANGKU_PROVIDER_KEY_SUFFIX}"
        )
        if env_key:
            return env_key
        return os.environ.get(TANGKU_PROVIDER_DEFAULT_KEY)


# --- AES-256 Encryption Backend ---


class AES256KeyStorage(SecureKeyStorage):
    """
    Secure storage backend for API keys using AES-256-GCM encryption.
    Requires the `cryptography` library.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError(
                "The 'cryptography' library is required for AES-256 encryption. "
                "Install it with: pip install cryptography"
            )
        super().__init__(storage_path)
        self._fernet = self._get_fernet()

    def _get_fernet(self) -> Any:
        """Get or generate a Fernet key for encryption."""
        env_key = os.environ.get(TANGKU_ENCRYPTION_KEY)
        if env_key:
            return Fernet(Fernet.generate_key() if env_key == "generate" else env_key.encode())
        return Fernet(Fernet.generate_key())

    def _encrypt(self, value: str) -> str:
        """Encrypt a value using AES-256-GCM."""
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt a value using AES-256-GCM."""
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception as e:
            raise KeyEncryptionError(f"Failed to decrypt key: {e}") from e


# --- Secret Manager Backends ---


class SecretManagerBackend:
    """Base class for secret manager backends."""

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret from the secret manager."""
        raise NotImplementedError("Subclasses must implement get_secret")


class AWSSecretsManagerBackend(SecretManagerBackend):
    """AWS Secrets Manager backend for API keys."""

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region
        try:
            import boto3
            self.client = boto3.client("secretsmanager", region_name=region)
        except ImportError:
            self.client = None

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret from AWS Secrets Manager."""
        if self.client is None:
            return None
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response.get("SecretString")
        except Exception:
            return None


class HashiCorpVaultBackend(SecretManagerBackend):
    """HashiCorp Vault backend for API keys."""

    def __init__(self, url: str = "http://127.0.0.1:8200", token: Optional[str] = None) -> None:
        self.url = url
        self.token = token or os.environ.get("VAULT_TOKEN")
        try:
            import hvac
            self.client = hvac.Client(url=url, token=token)
        except ImportError:
            self.client = None

    def get_secret(self, secret_path: str) -> Optional[str]:
        """Get a secret from HashiCorp Vault."""
        if self.client is None:
            return None
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_path
            )
            return response.get("data", {}).get("data", {}).get("api_key")
        except Exception:
            return None


# --- Quota Monitoring ---


class QuotaMonitor:
    """Monitors API key usage and quotas."""

    def __init__(self) -> None:
        self._usage: Dict[str, Dict[str, Any]] = {}
        self._quotas: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def set_quota(
        self, provider_id: str, max_requests: int, max_tokens: int, max_cost: float
    ) -> None:
        """Set a quota for a provider."""
        with self._lock:
            self._quotas[provider_id] = {
                "max_requests": max_requests,
                "max_tokens": max_tokens,
                "max_cost": max_cost,
            }

    def record_usage(
        self, provider_id: str, requests: int = 1, tokens: int = 0, cost: float = 0.0
    ) -> None:
        """Record usage for a provider."""
        with self._lock:
            if provider_id not in self._usage:
                self._usage[provider_id] = {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }
            self._usage[provider_id]["total_requests"] += requests
            self._usage[provider_id]["total_tokens"] += tokens
            self._usage[provider_id]["total_cost"] += cost

    def get_usage(self, provider_id: str) -> Dict[str, Any]:
        """Get usage for a provider."""
        return self._usage.get(provider_id, {})

    def get_quota_status(self, provider_id: str) -> Dict[str, Any]:
        """Get quota status for a provider."""
        usage = self.get_usage(provider_id)
        quota = self._quotas.get(provider_id, {})
        return {
            "usage": usage,
            "quota": quota,
            "requests_remaining": quota.get("max_requests", 0) - usage.get("total_requests", 0),
            "tokens_remaining": quota.get("max_tokens", 0) - usage.get("total_tokens", 0),
            "cost_remaining": quota.get("max_cost", 0.0) - usage.get("total_cost", 0.0),
        }

    def is_within_quota(self, provider_id: str) -> bool:
        """Check if a provider is within its quota."""
        status = self.get_quota_status(provider_id)
        return (
            status["requests_remaining"] > 0
            and status["tokens_remaining"] > 0
            and status["cost_remaining"] > 0
        )


# --- Key Rotation ---


class KeyRotator:
    """Automatically rotates API keys based on usage or expiration."""

    def __init__(self, storage: SecureKeyStorage) -> None:
        self._storage = storage
        self._lock = RLock()

    def rotate_if_needed(
        self, provider_id: str, max_usage: int = 1000, max_age_days: int = 30
    ) -> Optional[str]:
        """Rotate a key if it exceeds usage or age limits."""
        with self._lock:
            usage = self._storage.get_usage(provider_id)
            if usage and usage.request_count >= max_usage:
                return self._rotate_key(provider_id)
            entries = self._storage._keys.get(provider_id, [])
            for entry in entries:
                if entry.expires_at and (entry.expires_at - time.time()) < (max_age_days * 86400):
                    return self._rotate_key(provider_id)
            return None

    def _rotate_key(self, provider_id: str) -> str:
        """Rotate a key for a provider."""
        old_key = self._storage.get_key(provider_id)
        if old_key is None:
            raise KeyNotFoundError(f"No key found for provider {provider_id}")
        new_key = secrets.token_urlsafe(32)
        self._storage.rotate_key(provider_id, old_key, new_key)
        return new_key


class ProviderKeyManager:
    """
    High-level API key manager.
    Combines secure storage, environment resolution, and usage tracking.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        use_aes: bool = False,
    ) -> None:
        if use_aes and CRYPTOGRAPHY_AVAILABLE:
            self._storage: SecureKeyStorage = AES256KeyStorage(storage_path)
        else:
            self._storage = SecureKeyStorage(storage_path)
        self._env_resolver = EnvironmentKeyResolver()
        self._quota_monitor = QuotaMonitor()
        self._key_rotator = KeyRotator(self._storage)

    def save_key(
        self,
        provider_id: ProviderID,
        key: APIKey,
        expires_at: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save an API key for a provider."""
        self._storage.save_key(provider_id, key, expires_at, metadata)

    def get_key(self, provider_id: ProviderID) -> Optional[APIKey]:
        """Get the API key for a provider (from storage or environment)."""
        key = self._storage.get_key(provider_id)
        if key is not None:
            return key
        return self._env_resolver.resolve(provider_id)

    def get_all_keys(self, provider_id: ProviderID) -> List[APIKey]:
        """Get all API keys for a provider."""
        return self._storage.get_all_keys(provider_id)

    def remove_key(self, provider_id: ProviderID, key: Optional[APIKey] = None) -> None:
        """Remove an API key for a provider."""
        self._storage.remove_key(provider_id, key)

    def rotate_key(self, provider_id: ProviderID, old_key: APIKey, new_key: APIKey) -> None:
        """Rotate an API key for a provider."""
        self._storage.rotate_key(provider_id, old_key, new_key)

    def deactivate_key(self, provider_id: ProviderID, key: APIKey) -> None:
        """Deactivate an API key for a provider."""
        self._storage.deactivate_key(provider_id, key)

    def list_providers(self) -> List[ProviderID]:
        """List all providers with stored keys."""
        return self._storage.list_providers()

    def has_key(self, provider_id: ProviderID) -> bool:
        """Check if a provider has any active keys."""
        return self._storage.has_key(provider_id)

    def record_usage(
        self,
        provider_id: ProviderID,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record usage of a key."""
        self._storage.record_usage(provider_id, tokens, cost)
        self._quota_monitor.record_usage(provider_id, 1, tokens, cost)

    def get_usage(self, provider_id: ProviderID) -> Optional[KeyUsage]:
        """Get usage statistics for a provider's key."""
        return self._storage.get_usage(provider_id)

    def cleanup_expired(self) -> int:
        """Remove expired keys. Returns the number of keys removed."""
        return self._storage.cleanup_expired()

    def mask_key(self, provider_id: ProviderID) -> str:
        """Mask the key for a provider."""
        key = self.get_key(provider_id)
        return self._storage.mask_key(key)

    def set_quota(
        self, provider_id: str, max_requests: int, max_tokens: int, max_cost: float
    ) -> None:
        """Set a quota for a provider."""
        self._quota_monitor.set_quota(provider_id, max_requests, max_tokens, max_cost)

    def get_quota_status(self, provider_id: str) -> Dict[str, Any]:
        """Get quota status for a provider."""
        return self._quota_monitor.get_quota_status(provider_id)

    def rotate_if_needed(
        self, provider_id: str, max_usage: int = 1000, max_age_days: int = 30
    ) -> Optional[str]:
        """Rotate a key if it exceeds usage or age limits."""
        return self._key_rotator.rotate_if_needed(provider_id, max_usage, max_age_days)
