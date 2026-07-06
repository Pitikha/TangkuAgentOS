from __future__ import annotations

from threading import RLock

from .interfaces import SecretManager
from .models import Secret


class SecretManager(SecretManager):
    """Secret manager architecture."""

    def __init__(self) -> None:
        self._secrets: dict[str, Secret] = {}
        self._lock = RLock()

    def store_secret(self, secret: Secret) -> None:
        with self._lock:
            self._secrets[secret.secret_id] = secret

    def retrieve_secret(self, secret_id: str) -> Secret:
        with self._lock:
            return self._secrets[secret_id]
