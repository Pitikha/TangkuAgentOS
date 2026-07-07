from __future__ import annotations

from threading import RLock

from .models import SecurityConfiguration


class SecurityConfigurationManager:
    """Manage security configuration state."""

    def __init__(self) -> None:
        self._configuration = SecurityConfiguration(settings={"mode": "strict"})
        self._lock = RLock()

    def get_configuration(self) -> SecurityConfiguration:
        with self._lock:
            return self._configuration

    def set_configuration(self, configuration: SecurityConfiguration) -> None:
        with self._lock:
            self._configuration = configuration

    def update_setting(self, key: str, value: object) -> None:
        with self._lock:
            self._configuration.settings[key] = value
