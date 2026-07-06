from __future__ import annotations

from threading import RLock

from .models import PlanningConfiguration


class PlanningConfigurationManager:
    """Manage configuration for planning runtime."""

    def __init__(self) -> None:
        self._configuration = PlanningConfiguration(settings={"mode": "manual"})
        self._lock = RLock()

    def get_configuration(self) -> PlanningConfiguration:
        with self._lock:
            return self._configuration

    def update_setting(self, key: str, value: object) -> None:
        with self._lock:
            self._configuration.settings[key] = value
