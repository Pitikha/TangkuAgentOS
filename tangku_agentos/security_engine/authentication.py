from __future__ import annotations

from .interfaces import AuthenticationManager
from .models import Credential


class AuthenticationManager(AuthenticationManager):
    """Authentication manager architecture."""

    def authenticate(self, credentials: Credential) -> bool:
        return bool(credentials.identity) and bool(credentials.secret)
