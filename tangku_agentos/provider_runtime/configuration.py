from __future__ import annotations

import os

from .interfaces import ProviderConfiguration


class ProviderConfiguration(ProviderConfiguration):
    """Provider configuration abstraction with secret resolution and overrides."""

    def __init__(self, configuration: dict[str, object]) -> None:
        self._configuration = configuration

    def get_configuration(self) -> dict[str, object]:
        return self._configuration

    def get_secret(self, provider_id: str) -> str | None:
        if not provider_id:
            return None
        env_key = os.environ.get(f"TANGKU_PROVIDER_{provider_id.upper()}_KEY")
        if env_key:
            return env_key
        generic = os.environ.get("TANGKU_PROVIDER_KEY")
        if generic:
            return generic
        secret = self._configuration.get("api_key")
        if isinstance(secret, str):
            return secret
        return None
