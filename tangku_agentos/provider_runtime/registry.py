"""
TangkuAgentOS Provider Runtime - Provider Registry

This module implements a dynamic, extensible registry for AI providers.
It supports:
- Provider registration and discovery
- Versioning and capability tracking
- Plugin-based provider loading
- Lazy initialization
- Thread-safe operations
- Provider lifecycle management

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import (
        BaseProvider,
        ProviderID,
        ProviderCapability,
        ProviderDefinition,
        ProviderStatus,
        ModelConfiguration,
    )
    from .types import ProviderType

from .constants import ProviderStatus, ProviderType
from .exceptions import ProviderAlreadyExistsError, ProviderNotFoundError
from .interfaces import ProviderRegistryInterface


# =============================================================================
# Type Definitions
# =============================================================================

ProviderClass = Type[Any]  # Type for provider classes
ProviderFactoryFunc = Callable[..., Any]  # Type for provider factory functions


# =============================================================================
# Provider Metadata
# =============================================================================

class ProviderMetadata:
    """
    Metadata for a registered provider.

    Attributes:
        provider_id: Unique identifier for the provider.
        provider_class: Provider class.
        definition: Provider definition (e.g., capabilities, models).
        status: Current status of the provider.
        version: Provider version.
        is_default: If True, this provider is the default.
        is_enabled: If True, this provider is available for use.
        priority: Priority for routing (higher = more preferred).
    """

    def __init__(
        self,
        provider_id: ProviderID,
        provider_class: ProviderClass,
        definition: Optional[ProviderDefinition] = None,
        status: ProviderStatus = ProviderStatus.UNREGISTERED,
        version: str = "1.0.0",
        is_default: bool = False,
        is_enabled: bool = True,
        priority: int = 0,
    ):
        self.provider_id = provider_id
        self.provider_class = provider_class
        self.definition = definition or {
            "provider_id": provider_id,
            "display_name": provider_id,
            "provider_type": ProviderType.CUSTOM.value,
            "capabilities": {},
            "models": [],
            "metadata": {},
        }
        self.status = status
        self.version = version
        self.is_default = is_default
        self.is_enabled = is_enabled
        self.priority = priority

    def __repr__(self) -> str:
        return (
            f"ProviderMetadata("
            f"provider_id={self.provider_id!r}, "
            f"status={self.status!r}, "
            f"version={self.version!r}, "
            f"enabled={self.is_enabled})"
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Get the provider's capabilities."""
        return self.definition.get("capabilities", {})

    @property
    def display_name(self) -> str:
        """Get the provider's display name."""
        return self.definition.get("display_name", self.provider_id)

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider's type."""
        return self.definition.get("provider_type", ProviderType.CUSTOM)

    @property
    def models(self) -> List[str]:
        """Get the provider's supported models."""
        return self.definition.get("models", [])


# =============================================================================
# Provider Registry
# =============================================================================

class ProviderRegistry(ProviderRegistryInterface):
    """
    Central registry for all AI providers in TangkuAgentOS.

    Features:
    - Dynamic registration of providers
    - Plugin-based discovery
    - Version and capability tracking
    - Lazy initialization
    - Thread-safe operations
    - Provider lifecycle management

    Example:
        registry = ProviderRegistry()
        registry.register_provider(
            provider_id="openai",
            configuration={"api_key": "sk-..."},
            definition={
                "display_name": "OpenAI",
                "provider_type": "cloud",
                "capabilities": {"text": True, "chat": True},
            },
        )
        provider = registry.resolve_provider("openai")
    """

    def __init__(self) -> None:
        """Initialize the provider registry."""
        self._providers: Dict[ProviderID, ProviderMetadata] = {}
        self._instances: Dict[ProviderID, Any] = {}
        self._lock = RLock()
        self._plugins_loaded: bool = False

    def register_provider(
        self,
        provider_id: ProviderID,
        configuration: ModelConfiguration,
        definition: Optional[ProviderDefinition] = None,
    ) -> None:
        """
        Register a provider with the given configuration and definition.

        Args:
            provider_id: Unique identifier for the provider.
            configuration: Configuration for the provider.
            definition: Optional definition of the provider.

        Raises:
            ProviderAlreadyExistsError: If the provider is already registered.
        """
        with self._lock:
            if provider_id in self._providers:
                raise ProviderAlreadyExistsError(
                    f"Provider {provider_id!r} is already registered."
                )

            # Create metadata
            metadata = ProviderMetadata(
                provider_id=provider_id,
                provider_class=None,  # Will be set if a class is provided
                definition=definition,
                status=ProviderStatus.REGISTERED,
            )
            self._providers[provider_id] = metadata

    def register_provider_class(
        self,
        provider_id: ProviderID,
        provider_class: ProviderClass,
        definition: Optional[ProviderDefinition] = None,
        version: str = "1.0.0",
        is_default: bool = False,
        is_enabled: bool = True,
        priority: int = 0,
    ) -> None:
        """
        Register a provider class with the registry.

        Args:
            provider_id: Unique identifier for the provider.
            provider_class: Provider class (must inherit from BaseProvider).
            definition: Optional definition of the provider.
            version: Provider version.
            is_default: If True, this provider will be used by default.
            is_enabled: If True, this provider is available for use.
            priority: Priority for routing (higher = more preferred).

        Raises:
            ProviderAlreadyExistsError: If the provider is already registered.
        """
        with self._lock:
            if provider_id in self._providers:
                raise ProviderAlreadyExistsError(
                    f"Provider {provider_id!r} is already registered."
                )

            # Create metadata
            metadata = ProviderMetadata(
                provider_id=provider_id,
                provider_class=provider_class,
                definition=definition,
                status=ProviderStatus.REGISTERED,
                version=version,
                is_default=is_default,
                is_enabled=is_enabled,
                priority=priority,
            )
            self._providers[provider_id] = metadata

            # If this is the first default provider, set it
            if is_default and not any(
                m.is_default for m in self._providers.values()
            ):
                metadata.is_default = True

    def resolve_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """
        Resolve a provider's configuration by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ModelConfiguration: The provider's configuration.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            # Return a dummy configuration (actual config is managed elsewhere)
            return {"provider_id": provider_id}

    def list_providers(self) -> List[ProviderID]:
        """
        List all registered provider IDs.

        Returns:
            List[ProviderID]: List of all registered provider IDs.
        """
        with self._lock:
            return list(self._providers.keys())

    def unregister_provider(self, provider_id: ProviderID) -> None:
        """
        Unregister a provider by ID.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            del self._providers[provider_id]
            if provider_id in self._instances:
                del self._instances[provider_id]

    def get_definition(self, provider_id: ProviderID) -> Optional[ProviderDefinition]:
        """
        Get the definition for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Optional[ProviderDefinition]: The provider's definition, or None if not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            return self._providers[provider_id].definition

    def get_status(self, provider_id: ProviderID) -> ProviderStatus:
        """
        Get the status for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ProviderStatus: The current status of the provider.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            return self._providers[provider_id].status

    def set_status(self, provider_id: ProviderID, status: ProviderStatus) -> None:
        """
        Set the status for a provider.

        Args:
            provider_id: Unique identifier for the provider.
            status: New status for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            self._providers[provider_id].status = status

    def get_capabilities(self, provider_id: ProviderID) -> Dict[ProviderCapability, bool]:
        """
        Get the capabilities for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Dict[ProviderCapability, bool]: Dictionary of capabilities and their availability.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            return self._providers[provider_id].capabilities

    def has_capability(self, provider_id: ProviderID, capability: ProviderCapability) -> bool:
        """
        Check if a provider has a specific capability.

        Args:
            provider_id: Unique identifier for the provider.
            capability: Capability to check.

        Returns:
            bool: True if the provider has the capability, False otherwise.
        """
        return self.get_capabilities(provider_id).get(capability, False)

    def filter_by_capability(self, capability: ProviderCapability) -> List[ProviderID]:
        """
        Filter providers by a specific capability.

        Args:
            capability: Capability to filter by.

        Returns:
            List[ProviderID]: List of provider IDs that have the capability.
        """
        with self._lock:
            return [
                pid
                for pid, metadata in self._providers.items()
                if metadata.capabilities.get(capability, False)
            ]

    def filter_by_status(self, status: ProviderStatus) -> List[ProviderID]:
        """
        Filter providers by status.

        Args:
            status: Status to filter by.

        Returns:
            List[ProviderID]: List of provider IDs with the given status.
        """
        with self._lock:
            return [
                pid
                for pid, metadata in self._providers.items()
                if metadata.status == status
            ]

    def filter_by_type(self, provider_type: ProviderType) -> List[ProviderID]:
        """
        Filter providers by type.

        Args:
            provider_type: Type to filter by.

        Returns:
            List[ProviderID]: List of provider IDs with the given type.
        """
        with self._lock:
            return [
                pid
                for pid, metadata in self._providers.items()
                if metadata.provider_type == provider_type
            ]

    def get_provider_info(self, provider_id: ProviderID) -> Dict[str, Any]:
        """
        Get comprehensive info for a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            Dict[str, Any]: Dictionary containing provider info.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            metadata = self._providers[provider_id]
            return {
                "provider_id": provider_id,
                "display_name": metadata.display_name,
                "provider_type": metadata.provider_type,
                "status": metadata.status,
                "version": metadata.version,
                "is_default": metadata.is_default,
                "is_enabled": metadata.is_enabled,
                "priority": metadata.priority,
                "capabilities": metadata.capabilities,
                "models": metadata.models,
            }

    def list_provider_info(self) -> List[Dict[str, Any]]:
        """
        List comprehensive info for all providers.

        Returns:
            List[Dict[str, Any]]: List of provider info dictionaries.
        """
        with self._lock:
            return [self.get_provider_info(pid) for pid in self._providers]

    def get_provider_class(self, provider_id: ProviderID) -> ProviderClass:
        """
        Get the provider class for a registered provider.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ProviderClass: The provider class.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            return self._providers[provider_id].provider_class

    def get_instance(self, provider_id: ProviderID, **kwargs: Any) -> Any:
        """
        Get or create an instance of a provider.

        Args:
            provider_id: Unique identifier for the provider.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Any: Provider instance.

        Raises:
            ProviderNotFoundError: If the provider is not found or disabled.
        """
        with self._lock:
            metadata = self._providers.get(provider_id)
            if metadata is None:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            if not metadata.is_enabled:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is disabled."
                )

            if provider_id not in self._instances:
                if metadata.provider_class is None:
                    raise ProviderNotFoundError(
                        f"Provider {provider_id!r} has no associated class."
                    )
                self._instances[provider_id] = metadata.provider_class(**kwargs)

            return self._instances[provider_id]

    def enable_provider(self, provider_id: ProviderID) -> None:
        """
        Enable a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            self._providers[provider_id].is_enabled = True

    def disable_provider(self, provider_id: ProviderID) -> None:
        """
        Disable a provider.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            self._providers[provider_id].is_enabled = False

    def set_default_provider(self, provider_id: ProviderID) -> None:
        """
        Set the default provider.

        Args:
            provider_id: Unique identifier for the provider.

        Raises:
            ProviderNotFoundError: If the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(
                    f"Provider {provider_id!r} is not registered."
                )
            for metadata in self._providers.values():
                metadata.is_default = False
            self._providers[provider_id].is_default = True

    def get_default_provider(self) -> Optional[ProviderID]:
        """
        Get the default provider ID.

        Returns:
            Optional[ProviderID]: Default provider ID, or None if not set.
        """
        with self._lock:
            for pid, metadata in self._providers.items():
                if metadata.is_default and metadata.is_enabled:
                    return pid
            return None

    def load_plugins(self, package: str = "tangku_agentos.provider_runtime.providers") -> None:
        """
        Load providers from a Python package as plugins.

        Args:
            package: Package to scan for providers.
        """
        if self._plugins_loaded:
            return

        try:
            module = importlib.import_module(package)
            for _, submodule_name, _ in pkgutil.iter_modules(module.__path__):
                submodule = importlib.import_module(f"{package}.{submodule_name}")
                for attr_name in dir(submodule):
                    attr = getattr(submodule, attr_name)
                    if (
                        isinstance(attr, type)
                        and hasattr(attr, "provider_id")
                        and hasattr(attr, "capabilities")
                    ):
                        # Register the provider class
                        provider_id = getattr(attr, "provider_id")
                        capabilities = getattr(attr, "capabilities", {})
                        definition = getattr(attr, "definition", None)
                        self.register_provider_class(
                            provider_id=provider_id,
                            provider_class=attr,
                            definition=definition,
                        )
        except ImportError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load plugins from {package!r}: {e}")

        self._plugins_loaded = True

    def clear_instances(self) -> None:
        """Clear all provider instances (useful for testing)."""
        with self._lock:
            for instance in self._instances.values():
                try:
                    if hasattr(instance, "close"):
                        instance.close()
                except Exception:
                    pass
            self._instances.clear()


# =============================================================================
# Global Registry Instance
# =============================================================================

# Singleton registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """
    Get the global provider registry instance.

    Returns:
        ProviderRegistry: Global registry instance.
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_registry() -> None:
    """
    Reset the global provider registry (useful for testing).
    """
    global _registry
    if _registry is not None:
        _registry.clear_instances()
    _registry = None