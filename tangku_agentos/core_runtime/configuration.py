from __future__ import annotations

import os
import time
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Set

from .base import Configurable
from .constants import DEFAULT_CONFIG_NAMESPACE
from .exceptions import (
    ConfigurationError,
    MissingRequiredKeyError,
    SchemaValidationError,
)
from .types import ConfigData, ConfigKey, ConfigValue, ConfigurationSchema


class ConfigurationManager(Configurable):
    """
    Production-grade configuration manager with:
    - Schema validation (nested, required keys)
    - Environment variable support
    - Configuration versioning
    - Hot reload
    - Runtime validation
    """

    def __init__(
        self,
        schema: Optional[ConfigurationSchema] = None,
        namespace: str = DEFAULT_CONFIG_NAMESPACE,
    ) -> None:
        self._schema = schema or ConfigurationSchema()
        self._namespace = namespace
        self._configuration: ConfigData = self._schema.defaults.copy()
        self._lock = RLock()
        self._version = 1
        self._last_reload_time = 0.0
        self._reload_handlers: List[Callable[[ConfigData], None]] = []
        self._env_prefix = f"{self._namespace.upper()}_"

    @property
    def configuration(self) -> ConfigData:
        """Get a copy of the current configuration."""
        with self._lock:
            return self._configuration.copy()

    @property
    def version(self) -> int:
        """Get the current configuration version."""
        with self._lock:
            return self._version

    @property
    def last_reload_time(self) -> float:
        """Get the timestamp of the last reload."""
        with self._lock:
            return self._last_reload_time

    def get(self, key: ConfigKey, default: ConfigValue | None = None) -> ConfigValue | None:
        """Get a configuration value by key."""
        with self._lock:
            return self._configuration.get(key, default)

    def get_env(self, key: ConfigKey, default: ConfigValue | None = None) -> ConfigValue | None:
        """Get a configuration value from environment variables."""
        env_key = f"{self._env_prefix}{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)
        return self.get(key, default)

    def _parse_env_value(self, value: str) -> ConfigValue:
        """Parse an environment variable value into a ConfigValue."""
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "none":
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def configure(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        """Update the configuration with new values and validate."""
        with self._lock:
            self._validate(configuration)
            self._configuration.update(configuration)
            self._version += 1

    def update(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        """Alias for configure."""
        self.configure(configuration)

    def as_dict(self) -> ConfigData:
        """Get the configuration as a dictionary."""
        return self.configuration

    def _validate(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        """Validate the configuration against the schema."""
        if self._schema.validators:
            invalid_keys: List[str] = []
            for key, value in configuration.items():
                validator = self._schema.validators.get(key)
                if validator and not validator(value):
                    invalid_keys.append(key)
            if invalid_keys:
                raise SchemaValidationError(
                    f"Invalid values for configuration keys: {', '.join(invalid_keys)}"
                )

        if self._schema.required_keys:
            missing_keys = [
                key for key in self._schema.required_keys if key not in self._configuration
            ]
            if missing_keys:
                raise MissingRequiredKeyError(
                    f"Missing required configuration keys: {', '.join(missing_keys)}"
                )

        if self._schema.nested_schemas:
            for key, nested_schema in self._schema.nested_schemas.items():
                if key in configuration:
                    nested_config = configuration[key]
                    if not isinstance(nested_config, dict):
                        raise SchemaValidationError(
                            f"Nested configuration for '{key}' must be a dictionary."
                        )
                    # Recursively validate nested configuration
                    nested_manager = ConfigurationManager(nested_schema, self._namespace)
                    nested_manager._validate(nested_config)

    def ensure_required(self, required_keys: Iterable[ConfigKey]) -> None:
        """Ensure that the specified keys are present in the configuration."""
        missing_keys = [key for key in required_keys if key not in self._configuration]
        if missing_keys:
            raise MissingRequiredKeyError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """Load configuration from environment variables with the given prefix."""
        env_prefix = prefix or self._env_prefix
        env_config: ConfigData = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix) :].lower()
                env_config[config_key] = self._parse_env_value(value)
        if env_config:
            self.configure(env_config)

    def hot_reload(self) -> None:
        """Reload the configuration from environment variables and notify handlers."""
        old_config = self.configuration
        self.load_from_env()
        with self._lock:
            self._last_reload_time = time.time()
            self._version += 1
        if old_config != self.configuration:
            self._notify_reload_handlers(old_config)

    def register_reload_handler(self, handler: Callable[[ConfigData], None]) -> None:
        """Register a handler to be called on configuration reload."""
        with self._lock:
            self._reload_handlers.append(handler)

    def deregister_reload_handler(self, handler: Callable[[ConfigData], None]) -> None:
        """Deregister a reload handler."""
        with self._lock:
            self._reload_handlers = [h for h in self._reload_handlers if h != handler]

    def _notify_reload_handlers(self, old_config: ConfigData) -> None:
        """Notify all reload handlers of a configuration change."""
        for handler in self._reload_handlers:
            try:
                handler(self.configuration)
            except Exception as e:
                raise ConfigurationError(
                    f"Reload handler failed: {e}"
                ) from e

    def reset_to_defaults(self) -> None:
        """Reset the configuration to the schema defaults."""
        with self._lock:
            self._configuration = self._schema.defaults.copy()
            self._version += 1

    def get_nested(self, keys: List[ConfigKey]) -> ConfigValue | None:
        """Get a nested configuration value by a list of keys."""
        current = self.configuration
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def set_nested(self, keys: List[ConfigKey], value: ConfigValue) -> None:
        """Set a nested configuration value by a list of keys."""
        current = self.configuration
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        with self._lock:
            self._version += 1
