from __future__ import annotations

from typing import Any

from .hub import ProviderHub


class FirstRunWizard:
    """Interactive, headless, and CLI-first-run setup wizard."""

    def __init__(self, hub: ProviderHub) -> None:
        self._hub = hub

    def run(self, mode: str = "interactive", config: dict[str, Any] | None = None) -> dict[str, Any]:
        config = config or {}
        self._hub.detect_environment()
        if config.get("offline_mode"):
            self._hub.register_provider("ollama", {"base_url": "http://127.0.0.1:11434"}, capabilities={"chat": True, "offline": True})
        if mode == "headless":
            default_provider = config.get("default_provider", self._hub.resolve_default_provider())
            return {
                "status": "completed",
                "mode": mode,
                "default_provider": default_provider,
                "offline_mode": bool(config.get("offline_mode")),
                "hardware": self._hub.detect_hardware(),
            }
        return {"status": "completed", "mode": mode, "default_provider": self._hub.resolve_default_provider(), "hardware": self._hub.detect_hardware()}
