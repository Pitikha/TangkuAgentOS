"""Provider registry for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..model_runtime.models import ModelConfiguration
    from .types import ProviderCapability, ProviderDefinition, ProviderID, ProviderStatus

from .constants import ProviderStatus, ProviderType
from .exceptions import ProviderAlreadyExistsError, ProviderNotFoundError
from .interfaces import ProviderRegistryInterface


class ProviderRegistry(ProviderRegistryInterface):
    """
    Registry for provider configurations.
    Supports dynamic registration, resolution, and capability tracking.
    """

    def __init__(self) -> None:
        self._providers: Dict[ProviderID, ModelConfiguration] = {}
        self._definitions: Dict[ProviderID, ProviderDefinition] = {}
        self._status: Dict[ProviderID, ProviderStatus] = {}
        self._lock = RLock()

    def register_provider(
        self,
        provider_id: ProviderID,
        configuration: ModelConfiguration,
        definition: Optional[ProviderDefinition] = None,
    ) -> None:
        """
        Register a provider with the given configuration and definition.
        Raises ProviderAlreadyExistsError if the provider is already registered.
        """
        with self._lock:
            if provider_id in self._providers:
                raise ProviderAlreadyExistsError(f"Provider {provider_id} already exists")
            self._providers[provider_id] = configuration
            if definition is not None:
                self._definitions[provider_id] = definition
            self._status[provider_id] = ProviderStatus.REGISTERED

    def resolve_provider(self, provider_id: ProviderID) -> ModelConfiguration:
        """
        Resolve a provider's configuration by ID.
        Raises ProviderNotFoundError if the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider {provider_id} not found")
            return self._providers[provider_id]

    def list_providers(self) -> List[ProviderID]:
        """List all registered provider IDs."""
        with self._lock:
            return list(self._providers.keys())

    def unregister_provider(self, provider_id: ProviderID) -> None:
        """
        Unregister a provider by ID.
        Raises ProviderNotFoundError if the provider is not found.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider {provider_id} not found")
            del self._providers[provider_id]
            self._definitions.pop(provider_id, None)
            self._status.pop(provider_id, None)

    def get_definition(self, provider_id: ProviderID) -> Optional[ProviderDefinition]:
        """Get the definition for a provider."""
        with self._lock:
            return self._definitions.get(provider_id)

    def get_status(self, provider_id: ProviderID) -> ProviderStatus:
        """Get the status for a provider."""
        with self._lock:
            return self._status.get(provider_id, ProviderStatus.UNREGISTERED)

    def set_status(self, provider_id: ProviderID, status: ProviderStatus) -> None:
        """Set the status for a provider."""
        with self._lock:
            self._status[provider_id] = status

    def get_capabilities(self, provider_id: ProviderID) -> Dict[ProviderCapability, bool]:
        """Get the capabilities for a provider."""
        with self._lock:
            definition = self._definitions.get(provider_id)
            if definition is not None:
                return definition.capabilities
            return {}

    def has_capability(self, provider_id: ProviderID, capability: ProviderCapability) -> bool:
        """Check if a provider has a specific capability."""
        return self.get_capabilities(provider_id).get(capability, False)

    def filter_by_capability(self, capability: ProviderCapability) -> List[ProviderID]:
        """Filter providers by a specific capability."""
        with self._lock:
            return [
                provider_id
                for provider_id in self._providers
                if self.has_capability(provider_id, capability)
            ]

    def filter_by_status(self, status: ProviderStatus) -> List[ProviderID]:
        """Filter providers by status."""
        with self._lock:
            return [
                provider_id
                for provider_id, provider_status in self._status.items()
                if provider_status == status
            ]

    def filter_by_type(self, provider_type: ProviderType) -> List[ProviderID]:
        """Filter providers by type."""
        with self._lock:
            return [
                provider_id
                for provider_id, definition in self._definitions.items()
                if definition.provider_type == provider_type
            ]

    def get_provider_info(self, provider_id: ProviderID) -> Dict[str, Any]:
        """Get comprehensive info for a provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderNotFoundError(f"Provider {provider_id} not found")
            return {
                "provider_id": provider_id,
                "configuration": self._providers[provider_id],
                "definition": self._definitions.get(provider_id),
                "status": self._status.get(provider_id, ProviderStatus.UNREGISTERED),
                "capabilities": self.get_capabilities(provider_id),
            }

    def list_provider_info(self) -> List[Dict[str, Any]]:
        """List comprehensive info for all providers."""
        with self._lock:
            return [self.get_provider_info(provider_id) for provider_id in self._providers]
