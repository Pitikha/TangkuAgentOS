from __future__ import annotations

from threading import RLock
from typing import Any, Dict

from .models import Configuration


class ConfigurationManager:
    def __init__(self) -> None:
        self._configurations: Dict[str, Configuration] = {}
        self._lock = RLock()

    def register(self, configuration: Configuration) -> None:
        with self._lock:
            self._configurations[configuration.config_id] = configuration

    def get(self, config_id: str) -> Configuration | None:
        with self._lock:
            return self._configurations.get(config_id)

    def list(self) -> dict[str, Configuration]:
        with self._lock:
            return dict(self._configurations)

    def update(self, config_id: str, settings: dict[str, Any]) -> None:
        with self._lock:
            configuration = self._configurations.get(config_id)
            if configuration is not None:
                self._configurations[config_id] = Configuration(config_id=config_id, settings={**configuration.settings, **settings})
