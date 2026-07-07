from __future__ import annotations


class SDKFactory:
    """SDK factory contract."""

    def create(self, sdk_type: str) -> "SDKInterface":
        raise NotImplementedError
