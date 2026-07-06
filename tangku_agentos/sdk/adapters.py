from __future__ import annotations


class SDKAdapter:
    """Adapter contract for SDK extensions."""

    def adapt(self, interface: "SDKInterface") -> "SDKInterface":
        raise NotImplementedError
