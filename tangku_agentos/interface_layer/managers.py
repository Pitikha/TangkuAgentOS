from __future__ import annotations


class InterfaceManager:
    """Manages interface adapters."""

    def register_interface(self, interface: "ABC") -> None:
        raise NotImplementedError

    def get_interface(self, interface_name: str) -> "ABC":
        raise NotImplementedError
