from __future__ import annotations

from abc import ABC
from typing import Any

from .interfaces import ProviderAdapter


class ProviderAdapter(ProviderAdapter):
    """Base provider adapter."""

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
