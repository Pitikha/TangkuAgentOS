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
        env_key = os.environ.get("TANGKU_KEY_ENCRYPTION_KEY")
        if env_key:
            return hashlib.sha256(env_key.encode()).digest()
        return hashlib.sha256("tangku-provider-runtime".encode()).digest()

    def _encrypt(self, value: str) -> str:
        """Encrypt a value using XOR with the encryption key."""
        encoded = value.encode("utf-8")
        encrypted = bytes(b ^ self._encryption_key[i % len(self._encryption_key)] for i, b in enumerate(encoded))
        return base64.b64encode(encrypted).decode("utf-8")

    def _decrypt(self, value: str) -> str:
        """Decrypt a value using XOR with the encryption key."""
        try:
            encrypted = base64.b64decode(value.encode("utf-8"))
            decrypted = bytes(b ^ self._encryption_key[i % len(self._encryption_key)] for i, b in enumerate(encrypted))
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
            return any(entry.is_active and (entry.expires_at is None or entry.expires_at > time.time()) for entry in entries)

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
        env_key = os.environ.get(f"{TANGKU_PROVIDER_KEY_PREFIX}{provider_id.upper()}{TANGKU_PROVIDER_KEY_SUFFIX}")
        if env_key:
            return env_key
        return os.environ.get(TANGKU_PROVIDER_DEFAULT_KEY)


class ProviderKeyManager:
    """
    High-level API key manager.
    Combines secure storage, environment resolution, and usage tracking.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self._storage = SecureKeyStorage(storage_path)
        self._env_resolver = EnvironmentKeyResolver()

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
