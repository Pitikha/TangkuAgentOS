from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Iterable, Mapping, Optional

from .base import Configurable
from .exceptions import ConfigurationError
from .types import ConfigData, ConfigKey, ConfigValue, ConfigurationSchema


class ConfigurationManager(Configurable):
    """Core configuration manager for the Tangku kernel."""

    def __init__(self, schema: ConfigurationSchema) -> None:
        self._schema = schema
        self._configuration: ConfigData = schema.defaults.copy()
        self._lock = RLock()

    @property
    def configuration(self) -> ConfigData:
        with self._lock:
            return self._configuration.copy()

    def get(self, key: ConfigKey, default: ConfigValue | None = None) -> ConfigValue | None:
        with self._lock:
            return self._configuration.get(key, default)

    def configure(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        with self._lock:
            self._validate(configuration)
            self._configuration.update(configuration)

    def update(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        self.configure(configuration)

    def as_dict(self) -> ConfigData:
        return self.configuration

    def _validate(self, configuration: Mapping[ConfigKey, ConfigValue]) -> None:
        if self._schema.validators is None:
            return

        invalid_keys: list[str] = []
        for key, value in configuration.items():
            validator = self._schema.validators.get(key)
            if validator and not validator(value):
                invalid_keys.append(key)

        if invalid_keys:
            raise ConfigurationError(
                f"Invalid values for configuration keys: {', '.join(invalid_keys)}"
            )

    def ensure_required(self, required_keys: Iterable[ConfigKey]) -> None:
        missing_keys = [key for key in required_keys if key not in self._configuration]
        if missing_keys:
            raise ConfigurationError(f"Missing required configuration keys: {', '.join(missing_keys)}")
