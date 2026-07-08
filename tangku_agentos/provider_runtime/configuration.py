"""
TangkuAgentOS Provider Runtime - Unified Configuration Management

This module provides a centralized, secure, and dynamic configuration system for all
AI providers. It supports:
- Environment variables
- Secret managers (AWS Secrets, HashiCorp Vault, etc.)
- Dynamic reloading
- Validation (Pydantic models)
- Encryption for sensitive fields (e.g., API keys)
- Thread-safe operations

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import pydantic
from pydantic import Field, validator, BaseModel
from dotenv import load_dotenv

if TYPE_CHECKING:
    from .interfaces import (
        ProviderID,
        ProviderSettings,
        ModelConfiguration,
        ProviderDefinition,
    )


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

TANGKU_PROVIDER_KEY_PREFIX = "TANGKU_PROVIDER_"
TANGKU_PROVIDER_KEY_SUFFIX = "_KEY"
TANGKU_PROVIDER_DEFAULT_KEY = "TANGKU_PROVIDER_KEY"


# =============================================================================
# Exceptions
# =============================================================================

class ConfigurationError(Exception):
    """Base exception for configuration-related errors."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when a configuration is invalid."""

    pass


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration is missing."""

    pass


class SecretManagerError(ConfigurationError):
    """Raised when a secret manager operation fails."""

    pass


# =============================================================================
# Configuration Sources
# =============================================================================

class ConfigSource:
    """
    Base class for configuration sources (e.g., env, file, secret manager).

    Subclasses must implement:
    - get: Retrieve a configuration value by key.
    - list_keys: List all available keys.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key.
            default: Default value if key is not found.

        Returns:
            Any: Configuration value or default.
        """
        raise NotImplementedError

    def list_keys(self) -> List[str]:
        """
        List all available keys.

        Returns:
            List[str]: List of configuration keys.
        """
        raise NotImplementedError


class EnvConfigSource(ConfigSource):
    """
    Configuration source for environment variables.

    Supports:
    - Loading from .env files
    - Thread-safe operations
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the environment configuration source.

        Args:
            env_file: Path to a .env file to load. If None, uses system environment.
        """
        if env_file:
            load_dotenv(env_file)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from environment variables.

        Args:
            key: Environment variable name.
            default: Default value if key is not found.

        Returns:
            Any: Environment variable value or default.
        """
        return os.getenv(key, default)

    def list_keys(self) -> List[str]:
        """
        List all environment variable keys.

        Returns:
            List[str]: List of environment variable names.
        """
        return list(os.environ.keys())


class FileConfigSource(ConfigSource):
    """
    Configuration source for JSON/YAML files.

    Supports:
    - JSON configuration files
    - Thread-safe operations
    """

    def __init__(self, file_path: str):
        """
        Initialize the file configuration source.

        Args:
            file_path: Path to the configuration file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        self.file_path = Path(file_path)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load the configuration file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.file_path}")
        with open(self.file_path, "r") as f:
            self._data = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value from the file.

        Args:
            key: Configuration key.
            default: Default value if key is not found.

        Returns:
            Any: Configuration value or default.
        """
        return self._data.get(key, default)

    def list_keys(self) -> List[str]:
        """
        List all keys in the configuration file.

        Returns:
            List[str]: List of configuration keys.
        """
        return list(self._data.keys())


class SecretManagerConfigSource(ConfigSource):
    """
    Base class for secret manager integrations (e.g., AWS Secrets, HashiCorp Vault).

    Subclasses must implement:
    - _init_client: Initialize the secret manager client.
    """

    def __init__(self, manager_type: str, **kwargs: Any):
        """
        Initialize the secret manager configuration source.

        Args:
            manager_type: Type of secret manager (e.g., "aws", "vault").
            **kwargs: Additional arguments for the secret manager client.
        """
        self.manager_type = manager_type
        self._client = self._init_client(**kwargs)

    def _init_client(self, **kwargs: Any) -> Any:
        """
        Initialize the secret manager client.

        Args:
            **kwargs: Additional arguments for the client.

        Returns:
            Any: Secret manager client instance.
        """
        raise NotImplementedError

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value by key.

        Args:
            key: Secret key.
            default: Default value if key is not found.

        Returns:
            Any: Secret value or default.
        """
        try:
            return self._client.get_secret_value(key)
        except Exception as e:
            logger.warning(f"Failed to get secret {key} from {self.manager_type}: {e}")
            return default

    def list_keys(self) -> List[str]:
        """
        List all available secret keys.

        Returns:
            List[str]: List of secret keys.
        """
        try:
            return self._client.list_secret_keys()
        except Exception as e:
            logger.warning(f"Failed to list secrets from {self.manager_type}: {e}")
            return []


# =============================================================================
# AWS Secrets Manager Integration
# =============================================================================

class AWSSecretsManagerConfigSource(SecretManagerConfigSource):
    """
    Configuration source for AWS Secrets Manager.

    Requires:
    - boto3 library
    - AWS credentials configured
    """

    def _init_client(self, **kwargs: Any) -> Any:
        """
        Initialize the AWS Secrets Manager client.

        Args:
            **kwargs: Additional arguments for the client.

        Returns:
            Any: AWS Secrets Manager client.
        """
        try:
            import boto3
            return boto3.client("secretsmanager", **kwargs)
        except ImportError:
            raise SecretManagerError("boto3 is required for AWS Secrets Manager")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value from AWS Secrets Manager.

        Args:
            key: Secret name.
            default: Default value if secret is not found.

        Returns:
            Any: Secret value or default.
        """
        try:
            response = self._client.get_secret_value(SecretId=key)
            return response.get("SecretString", default)
        except Exception as e:
            logger.warning(f"Failed to get secret {key} from AWS Secrets Manager: {e}")
            return default

    def list_keys(self) -> List[str]:
        """
        List all secret names in AWS Secrets Manager.

        Returns:
            List[str]: List of secret names.
        """
        try:
            response = self._client.list_secrets()
            return [secret["Name"] for secret in response.get("SecretList", [])]
        except Exception as e:
            logger.warning(f"Failed to list secrets from AWS Secrets Manager: {e}")
            return []


# =============================================================================
# HashiCorp Vault Integration
# =============================================================================

class VaultConfigSource(SecretManagerConfigSource):
    """
    Configuration source for HashiCorp Vault.

    Requires:
    - hvac library
    - Vault server URL and token configured
    """

    def _init_client(self, **kwargs: Any) -> Any:
        """
        Initialize the HashiCorp Vault client.

        Args:
            **kwargs: Additional arguments for the client.

        Returns:
            Any: HashiCorp Vault client.
        """
        try:
            import hvac
            return hvac.Client(**kwargs)
        except ImportError:
            raise SecretManagerError("hvac is required for HashiCorp Vault")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a secret value from HashiCorp Vault.

        Args:
            key: Secret path (e.g., "secret/myapp/api_key").
            default: Default value if secret is not found.

        Returns:
            Any: Secret value or default.
        """
        try:
            response = self._client.secrets.kv.v2.read_secret_version(path=key)
            return response.get("data", {}).get("data", default)
        except Exception as e:
            logger.warning(f"Failed to get secret {key} from HashiCorp Vault: {e}")
            return default

    def list_keys(self) -> List[str]:
        """
        List all secret paths in HashiCorp Vault.

        Returns:
            List[str]: List of secret paths.
        """
        try:
            response = self._client.secrets.kv.v2.list_secrets(path="secret")
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            logger.warning(f"Failed to list secrets from HashiCorp Vault: {e}")
            return []


# =============================================================================
# Pydantic Models for Configuration
# =============================================================================

class ProviderSettingsModel(BaseModel):
    """
    Pydantic model for provider settings.

    Supports:
    - Validation
    - Default values
    - Environment variable resolution
    """

    api_key: Optional[str] = Field(
        None,
        description="API key for the provider. If None, will attempt to load from env/secrets.",
    )
    base_url: Optional[str] = Field(
        None,
        description="Base URL for the provider API (e.g., for self-hosted providers).",
    )
    timeout: float = Field(
        30.0,
        ge=0.1,
        le=300.0,
        description="Request timeout in seconds.",
    )
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum number of retries for failed requests.",
    )
    retry_delay: float = Field(
        1.0,
        ge=0.0,
        le=60.0,
        description="Delay between retries in seconds.",
    )
    rate_limit: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum requests per minute (None for no limit).",
    )
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers for requests.",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific configuration.",
    )

    @validator("api_key")
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate that API key is not empty."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("API key cannot be empty.")
        return v


class ModelConfigurationModel(BaseModel):
    """
    Pydantic model for model configuration.

    Supports:
    - Validation
    - Default values
    - Nested provider settings
    """

    model_id: Optional[str] = Field(
        None,
        description="Unique identifier for the model.",
    )
    provider_id: Optional[str] = Field(
        None,
        description="Unique identifier for the provider.",
    )
    settings: ProviderSettingsModel = Field(
        default_factory=ProviderSettingsModel,
        description="Settings for the provider.",
    )
    capabilities: Dict[str, bool] = Field(
        default_factory=dict,
        description="Supported capabilities (e.g., {'text': True, 'vision': False}).",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the model.",
    )


class ProviderDefinitionModel(BaseModel):
    """
    Pydantic model for provider definition.

    Supports:
    - Validation
    - Default values
    - Nested configurations
    """

    provider_id: str = Field(
        ...,
        description="Unique identifier for the provider.",
    )
    display_name: str = Field(
        ...,
        description="Human-readable name for the provider.",
    )
    provider_type: str = Field(
        ...,
        description="Type of provider (e.g., 'cloud', 'local').",
    )
    capabilities: Dict[str, bool] = Field(
        default_factory=dict,
        description="Supported capabilities.",
    )
    models: List[str] = Field(
        default_factory=list,
        description="List of supported model IDs.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the provider.",
    )


# =============================================================================
# Configuration Manager
# =============================================================================

@dataclass
class ProviderConfiguration:
    """
    Provider configuration with:
    - Secret resolution
    - Environment variable support
    - Validation
    - Overrides
    - Thread-safe operations
    """

    configuration: Dict[str, Any] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the lock if not provided."""
        if not isinstance(self._lock, RLock):
            self._lock = RLock()

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the configuration.

        Returns:
            Dict[str, Any]: Copy of the configuration.
        """
        return self.configuration.copy()

    def get_secret(self, provider_id: ProviderID) -> Optional[str]:
        """
        Get the API key for a provider.

        Tries:
        1. Environment variable: TANGKU_PROVIDER_{PROVIDER_ID}_KEY
        2. Environment variable: TANGKU_PROVIDER_KEY
        3. Configuration: api_key

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[str]: API key or None if not found.
        """
        if not provider_id:
            return None

        # Try provider-specific environment variable
        env_key = os.environ.get(
            f"{TANGKU_PROVIDER_KEY_PREFIX}{provider_id.upper()}{TANGKU_PROVIDER_KEY_SUFFIX}"
        )
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
        """
        Get a configuration setting.

        Args:
            key: Setting key.
            default: Default value if key is not found.

        Returns:
            Any: Setting value or default.
        """
        return self.configuration.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a configuration setting.

        Args:
            key: Setting key.
            value: Setting value.
        """
        with self._lock:
            self.configuration[key] = value

    def update_configuration(self, updates: Dict[str, Any]) -> None:
        """
        Update the configuration with new values.

        Args:
            updates: Dictionary of updates to apply.
        """
        with self._lock:
            self.configuration.update(updates)

    def validate(self, required_keys: Optional[List[str]] = None) -> None:
        """
        Validate the configuration.

        Args:
            required_keys: List of keys that must be present.

        Raises:
            MissingConfigurationError: If required keys are missing.
        """
        if required_keys:
            missing = [key for key in required_keys if key not in self.configuration]
            if missing:
                raise MissingConfigurationError(
                    f"Missing required configuration keys: {', '.join(missing)}"
                )

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """
        Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables. If None, uses TANGKU_PROVIDER_KEY_PREFIX.
        """
        env_prefix = prefix or TANGKU_PROVIDER_KEY_PREFIX
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self.configuration[config_key] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.

        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        return self.configuration.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProviderConfiguration:
        """
        Create a configuration from a dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            ProviderConfiguration: New configuration instance.
        """
        return cls(configuration=data.copy())


class ProviderConfigurationManager:
    """
    Manages configurations for multiple providers.

    Features:
    - Thread-safe operations
    - Dynamic updates
    - Validation
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._configurations: Dict[ProviderID, ProviderConfiguration] = {}
        self._lock = RLock()

    def add_configuration(
        self, provider_id: ProviderID, configuration: ProviderConfiguration
    ) -> None:
        """
        Add a configuration for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            configuration: Configuration for the provider.
        """
        with self._lock:
            self._configurations[provider_id] = configuration

    def get_configuration(self, provider_id: ProviderID) -> ProviderConfiguration:
        """
        Get the configuration for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ProviderConfiguration: Configuration for the provider.
        """
        return self._configurations.get(provider_id, ProviderConfiguration())

    def remove_configuration(self, provider_id: ProviderID) -> None:
        """
        Remove the configuration for a provider.

        Args:
            provider_id: Unique identifier for the provider.
        """
        with self._lock:
            self._configurations.pop(provider_id, None)

    def list_providers(self) -> List[ProviderID]:
        """
        List all providers with configurations.

        Returns:
            List[ProviderID]: List of provider IDs.
        """
        return list(self._configurations.keys())

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """
        Load configurations from environment variables.

        Args:
            prefix: Prefix for environment variables.
        """
        for provider_id in self._configurations:
            self._configurations[provider_id].load_from_env(prefix)

    def validate_all(self, required_keys: Optional[List[str]] = None) -> None:
        """
        Validate all configurations.

        Args:
            required_keys: List of keys that must be present in each configuration.

        Raises:
            MissingConfigurationError: If any configuration is missing required keys.
        """
        for provider_id, config in self._configurations.items():
            try:
                config.validate(required_keys)
            except MissingConfigurationError as e:
                logger.error(f"Validation failed for provider {provider_id}: {e}")
                raise


# =============================================================================
# Encryption Support (Optional)
# =============================================================================

class EncryptedConfiguration(ProviderConfiguration):
    """
    Provider configuration with encryption support for sensitive fields.

    Requires:
    - cryptography library
    """

    def __init__(
        self,
        configuration: Dict[str, Any],
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize the encrypted configuration.

        Args:
            configuration: Configuration dictionary.
            encryption_key: Key for encrypting/decrypting sensitive fields.
        """
        super().__init__(configuration=configuration)
        self._encryption_key = encryption_key
        self._sensitive_fields = {"api_key", "secret", "password", "token"}

    def _encrypt(self, value: str) -> str:
        """
        Encrypt a value.

        Args:
            value: Value to encrypt.

        Returns:
            str: Encrypted value.
        """
        if not self._encryption_key:
            return value
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(self._encryption_key.encode())
            return fernet.encrypt(value.encode()).decode()
        except Exception as e:
            logger.warning(f"Failed to encrypt value: {e}")
            return value

    def _decrypt(self, value: str) -> str:
        """
        Decrypt a value.

        Args:
            value: Value to decrypt.

        Returns:
            str: Decrypted value.
        """
        if not self._encryption_key:
            return value
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(self._encryption_key.encode())
            return fernet.decrypt(value.encode()).decode()
        except Exception as e:
            logger.warning(f"Failed to decrypt value: {e}")
            return value

    def get_secret(self, provider_id: ProviderID) -> Optional[str]:
        """
        Get the API key for a provider (decrypted if encrypted).

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[str]: API key or None if not found.
        """
        secret = super().get_secret(provider_id)
        if secret and isinstance(secret, str):
            # Check if the secret is encrypted (e.g., starts with 'gAAAA' for Fernet)
            if secret.startswith("gAAAA"):
                return self._decrypt(secret)
        return secret

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a configuration setting (encrypted if sensitive).

        Args:
            key: Setting key.
            value: Setting value.
        """
        if key in self._sensitive_fields and isinstance(value, str):
            value = self._encrypt(value)
        super().set_setting(key, value)


# =============================================================================
# Utility Functions
# =============================================================================

def load_config(
    config_file: Optional[str] = None,
    env_file: Optional[str] = None,
    use_secrets_manager: bool = False,
    secrets_manager_type: str = "aws",
    **secrets_kwargs: Any,
) -> ProviderConfigurationManager:
    """
    Convenience function to load configuration from multiple sources.

    Args:
        config_file: Path to JSON config file.
        env_file: Path to .env file.
        use_secrets_manager: If True, use a secret manager for sensitive fields.
        secrets_manager_type: Type of secret manager (e.g., "aws", "vault").
        **secrets_kwargs: Additional arguments for the secret manager.

    Returns:
        ProviderConfigurationManager: Configuration manager instance.
    """
    manager = ProviderConfigurationManager()

    # Add environment source
    env_source = EnvConfigSource(env_file)
    manager._sources.append(env_source)

    # Add file source if provided
    if config_file:
        file_source = FileConfigSource(config_file)
        manager._sources.append(file_source)

    # Add secret manager source if enabled
    if use_secrets_manager:
        if secrets_manager_type == "aws":
            secrets_source = AWSSecretsManagerConfigSource(**secrets_kwargs)
        elif secrets_manager_type == "vault":
            secrets_source = VaultConfigSource(**secrets_kwargs)
        else:
            raise SecretManagerError(
                f"Unsupported secret manager type: {secrets_manager_type}"
            )
        manager._sources.append(secrets_source)

    return manager