from __future__ import annotations


class SDKBuilder:
    """Abstract SDK builder."""

    def build(self) -> "SDKInterface":
        raise NotImplementedError
