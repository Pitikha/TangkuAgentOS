"""First-run wizard for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .constants import ProviderID
from .hub import ProviderHub


class FirstRunWizard:
    """
    Interactive, headless, and CLI-first-run setup wizard.
    Supports:
    - Environment detection
    - Provider setup
    - Offline mode
    - Configuration generation
    """

    def __init__(self, hub: ProviderHub) -> None:
        self._hub = hub

    def run(
        self,
        mode: str = "interactive",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run the first-run wizard.
        Modes:
        - interactive: Interactive setup (not implemented in CLI)
        - headless: Non-interactive setup
        - cli: CLI setup
        """
        config = config or {}
        self._hub.detect_environment()

        if config.get("offline_mode"):
            self._setup_offline_mode()

        if mode == "headless":
            return self._run_headless(config)
        elif mode == "cli":
            return self._run_cli(config)
        else:
            return self._run_interactive(config)

    def _setup_offline_mode(self) -> None:
        """Set up offline mode with local providers."""
        self._hub.register_provider(
            "ollama",
            {"base_url": "http://127.0.0.1:11434"},
            capabilities={"chat": True, "offline": True},
        )

    def _run_headless(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the wizard in headless mode."""
        default_provider = config.get("default_provider", self._hub.resolve_default_provider())
        return {
            "status": "completed",
            "mode": "headless",
            "default_provider": default_provider,
            "offline_mode": bool(config.get("offline_mode")),
            "hardware": self._hub.detect_hardware(),
            "providers": self._hub.list_providers(),
        }

    def _run_cli(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the wizard in CLI mode."""
        return {
            "status": "completed",
            "mode": "cli",
            "default_provider": self._hub.resolve_default_provider(),
            "hardware": self._hub.detect_hardware(),
            "providers": self._hub.list_providers(),
        }

    def _run_interactive(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the wizard in interactive mode."""
        # Placeholder for interactive mode
        return {
            "status": "completed",
            "mode": "interactive",
            "default_provider": self._hub.resolve_default_provider(),
            "hardware": self._hub.detect_hardware(),
            "providers": self._hub.list_providers(),
        }

    def detect_providers(self) -> List[Dict[str, Any]]:
        """Detect available providers."""
        return self._hub.detect_environment().get("providers", [])

    def setup_provider(
        self,
        provider_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set up a provider with the given API key and base URL."""
        settings: Dict[str, Any] = {}
        if api_key:
            settings["api_key"] = api_key
        if base_url:
            settings["base_url"] = base_url
        return self._hub.register_provider(provider_id, settings)

    def generate_configuration(self) -> Dict[str, Any]:
        """Generate a configuration file for the provider runtime."""
        return {
            "providers": self._hub.list_providers(),
            "models": [model.get("model_id") for model in self._hub.list_models()],
            "hardware": self._hub.detect_hardware(),
        }

    def save_configuration(self, path: str) -> None:
        """Save the configuration to a file."""
        config = self.generate_configuration()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
