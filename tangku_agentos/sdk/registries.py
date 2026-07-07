from __future__ import annotations


class SDKRegistry:
    """SDK registration and lookup."""

    def register(self, sdk: "SDKInterface") -> None:
        raise NotImplementedError

    def resolve(self, sdk_id: str) -> "SDKInterface":
        raise NotImplementedError
