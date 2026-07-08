"""Configuration for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ProviderID

from .constants import TANGKU_PROVIDER_DEFAULT_KEY, TANGKU_PROVIDER_KEY_PREFIX, TANGKU_PROVIDER_KEY_SUFFIX
from .exceptions import InvalidConfigurationError, MissingConfigurationError


@dataclass
class ProviderConfiguration:
    """
    Provider configuration with:
    - Secret resolution
    - Environment variable support
    - Validation
    - Overrides
    """

    configuration: Dict[str, Any] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self._lock, RLock):
            self._lock = RLock()

    def get_configuration(self) -> Dict[str, Any]:
        """Get the configuration."""
        return self.configuration.copy()

    def get_secret(self, provider_id: ProviderID) -> Optional[str]:
        """
        Get the API key for a provider.
        Tries:
        1. Environment variable: TANGKU_PROVIDER_{PROVIDER_ID}_KEY
        2. Environment variable: TANGKU_PROVIDER_KEY
        3. Configuration: api_key
        """
        if not provider_id:
            return None

        # Try provider-specific environment variable
        env_key = os.environ.get(f"{TANGKU_PROVIDER_KEY_PREFIX}{provider_id.upper()}{TANGKU_PROVIDER_KEY_SUFFIX}")
        if env_key:
            return env_key

        # Try generic environment variable
        generic = os.environ.get(TANGKU_PROVIDER_DEFAULT_KEY)
        if generic:
            return generic

        # Try configuration
        secret = self.configuration.get("api_key")
        if isinstance(secret, str):
            return secret

        return None

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return self.configuration.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        with self._lock:
            self.configuration[key] = value

    def update_configuration(self, updates: Dict[str, Any]) -> None:
        """Update the configuration with new values."""
        with self._lock:
            self.configuration.update(updates)

    def validate(self, required_keys: Optional[List[str]] = None) -> None:
        """Validate the configuration."""
        if required_keys:
            missing = [key for key in required_keys if key not in self.configuration]
            if missing:
                raise MissingConfigurationError(f"Missing required configuration keys: {', '.join(missing)}")

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """Load configuration from environment variables."""
        env_prefix = prefix or TANGKU_PROVIDER_KEY_PREFIX
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self.configuration[config_key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return self.configuration.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProviderConfiguration:
        """Create a configuration from a dictionary."""
        return cls(configuration=data.copy())


class ProviderConfigurationManager:
    """Manages configurations for multiple providers."""

    def __init__(self) -> None:
        self._configurations: Dict[ProviderID, ProviderConfiguration] = {}
        self._lock = RLock()

    def add_configuration(
        self, provider_id: ProviderID, configuration: ProviderConfiguration
    ) -> None:
        """Add a configuration for a provider."""
        with self._lock:
            self._configurations[provider_id] = configuration

    def get_configuration(self, provider_id: ProviderID) -> ProviderConfiguration:
        """Get the configuration for a provider."""
        return self._configurations.get(provider_id, ProviderConfiguration())

    def remove_configuration(self, provider_id: ProviderID) -> None:
        """Remove the configuration for a provider."""
        with self._lock:
            self._configurations.pop(provider_id, None)

    def list_providers(self) -> List[ProviderID]:
        """List all providers with configurations."""
        return list(self._configurations.keys())

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """Load configurations from environment variables."""
        for provider_id in self._configurations:
            self._configurations[provider_id].load_from_env(prefix)

    def validate_all(self, required_keys: Optional[List[str]] = None) -> None:
        """Validate all configurations."""
        for provider_id, config in self._configurations.items():
            config.validate(required_keys)
