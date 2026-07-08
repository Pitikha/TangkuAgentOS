"""Provider factory for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from ..model_runtime.models import ModelConfiguration
    from .interfaces import ProviderAdapter, ProviderPlugin
    from .types import ProviderID, ProviderSettings

from .constants import ProviderID, ProviderType
from .exceptions import PluginLoadError, PluginNotFoundError, ProviderNotFoundError
from .interfaces import ProviderFactory
from .providers import CustomProvider


class PluginLoader:
    """Loads provider plugins dynamically."""

    def __init__(self, plugin_dirs: Optional[List[str]] = None) -> None:
        self._plugin_dirs = plugin_dirs or ["tangku_agentos/provider_runtime/plugins"]
        self._plugins: Dict[str, Type[ProviderPlugin]] = {}
        self._lock = RLock()

    def load_plugin(self, plugin_path: str) -> Type[ProviderPlugin]:
        """Load a plugin from the given path."""
        try:
            module_path = Path(plugin_path).with_suffix("")
            module_name = module_path.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Cannot load plugin from {plugin_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "ProviderPlugin"):
                raise PluginLoadError(f"Plugin {plugin_path} does not define a ProviderPlugin class")
            plugin_class = getattr(module, "ProviderPlugin")
            with self._lock:
                self._plugins[plugin_class.provider_id] = plugin_class
            return plugin_class
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {plugin_path}: {e}") from e

    def load_all_plugins(self) -> Dict[str, Type[ProviderPlugin]]:
        """Load all plugins from the configured directories."""
        with self._lock:
            for plugin_dir in self._plugin_dirs:
                if not Path(plugin_dir).exists():
                    continue
                for _, module_name, _ in pkgutil.iter_modules([plugin_dir]):
                    try:
                        module = importlib.import_module(f"{plugin_dir}.{module_name}")
                        if hasattr(module, "ProviderPlugin"):
                            plugin_class = getattr(module, "ProviderPlugin")
                            self._plugins[plugin_class.provider_id] = plugin_class
                    except Exception:
                        continue
            return self._plugins.copy()

    def unload_plugin(self, provider_id: ProviderID) -> None:
        """Unload a plugin by provider ID."""
        with self._lock:
            self._plugins.pop(provider_id, None)

    def get_plugin(self, provider_id: ProviderID) -> Optional[Type[ProviderPlugin]]:
        """Get a plugin by provider ID."""
        return self._plugins.get(provider_id)

    def list_plugins(self) -> List[ProviderID]:
        """List all loaded plugin IDs."""
        return list(self._plugins.keys())


class ProviderFactory(ProviderFactory):
    """
    Factory for creating provider adapters.
    Supports built-in providers, custom providers, and plugins.
    """

    def __init__(
        self,
        plugin_loader: Optional[PluginLoader] = None,
    ) -> None:
        self._plugin_loader = plugin_loader or PluginLoader()
        self._builtin_providers: Dict[ProviderID, Type[Any]] = {
            ProviderID.OPENAI.value: None,  # Lazy-loaded
            ProviderID.ANTHROPIC.value: None,
            ProviderID.GOOGLE.value: None,
            ProviderID.GROQ.value: None,
            ProviderID.DEEPSEEK.value: None,
            ProviderID.MISTRAL.value: None,
            ProviderID.COHERE.value: None,
            ProviderID.TOGETHER.value: None,
            ProviderID.FIREWORKS.value: None,
            ProviderID.AZURE_OPENAI.value: None,
            ProviderID.OPENROUTER.value: None,
            ProviderID.OLLAMA.value: None,
            ProviderID.LMSTUDIO.value: None,
            ProviderID.LLAMACPP.value: None,
            ProviderID.VLLM.value: None,
            ProviderID.LOCAL.value: None,
            ProviderID.CUSTOM.value: CustomProvider,
        }
        self._lock = RLock()

    def _lazy_load_builtin(self, provider_id: ProviderID) -> Type[Any]:
        """Lazy-load a built-in provider."""
        from .providers import (
            AnthropicProvider,
            DeepSeekProvider,
            GoogleProvider,
            GroqProvider,
            LocalModelProvider,
            LMStudioProvider,
            OllamaProvider,
            OpenAIProvider,
            OpenRouterProvider,
        )

        provider_map = {
            ProviderID.OPENAI.value: OpenAIProvider,
            ProviderID.ANTHROPIC.value: AnthropicProvider,
            ProviderID.GOOGLE.value: GoogleProvider,
            ProviderID.GROQ.value: GroqProvider,
            ProviderID.DEEPSEEK.value: DeepSeekProvider,
            ProviderID.OPENROUTER.value: OpenRouterProvider,
            ProviderID.OLLAMA.value: OllamaProvider,
            ProviderID.LMSTUDIO.value: LMStudioProvider,
            ProviderID.LLAMACPP.value: LocalModelProvider,
            ProviderID.VLLM.value: LocalModelProvider,
            ProviderID.AZURE_OPENAI.value: OpenAIProvider,
        }
        return provider_map.get(provider_id, CustomProvider)

    def register_provider(self, provider_id: ProviderID, provider_class: Type[Any]) -> None:
        """Register a custom provider class."""
        with self._lock:
            self._builtin_providers[provider_id] = provider_class

    def create(
        self,
        provider_id: ProviderID,
        configuration: ModelConfiguration,
    ) -> ProviderAdapter:
        """
        Create a provider adapter for the given ID and configuration.
        Tries plugins first, then built-in providers, then falls back to CustomProvider.
        """
        # Try plugins first
        plugin_class = self._plugin_loader.get_plugin(provider_id)
        if plugin_class is not None:
            instance = plugin_class()
            instance.initialize(configuration.settings)
            return instance

        # Try built-in providers
        provider_class = self._builtin_providers.get(provider_id)
        if provider_class is None:
            provider_class = self._lazy_load_builtin(provider_id)
        if provider_class is not None:
            return provider_class(provider_id, configuration.settings)

        # Fall back to CustomProvider
        return CustomProvider(provider_id, configuration.settings)

    def list_supported_providers(self) -> List[ProviderID]:
        """List all supported provider IDs."""
        with self._lock:
            supported = list(self._builtin_providers.keys())
            supported.extend(self._plugin_loader.list_plugins())
            return supported

    def load_plugin(self, plugin_path: str) -> None:
        """Load a plugin from the given path."""
        self._plugin_loader.load_plugin(plugin_path)

    def load_all_plugins(self) -> None:
        """Load all plugins from the configured directories."""
        self._plugin_loader.load_all_plugins()
