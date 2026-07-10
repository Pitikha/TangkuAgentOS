"""
AI Foundation Framework - Provider Registry

This module provides a registry for managing AI providers.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.providers.base import BaseProvider
    from tangku_agentos.ai_foundation.models.model import AIModel
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class RegistryStatus(Enum):
    """Status of the provider registry."""
    UNINITIALIZED = auto()
    READY = auto()
    ERROR = auto()


@dataclass
class RegistryMetrics:
    """Metrics for the provider registry."""
    providers_registered: int = 0
    providers_initialized: int = 0
    providers_started: int = 0
    models_available: int = 0
    requests_routed: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "providers_registered": self.providers_registered,
            "providers_initialized": self.providers_initialized,
            "providers_started": self.providers_started,
            "models_available": self.models_available,
            "requests_routed": self.requests_routed,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ProviderRegistry:
    """
    Registry for managing AI providers.
    
    This class provides a centralized way to register, manage, and access
    AI providers. It supports dynamic registration and unregistration
    of providers, and provides methods for routing requests to the
    appropriate provider.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ProviderRegistry
        >>> 
        >>> # Create registry
        >>> registry = ProviderRegistry()
        >>> 
        >>> # Register a provider
        >>> await registry.register_provider(my_provider)
        >>> 
        >>> # Get a provider
        >>> provider = registry.get_provider("my_provider")
        >>> 
        >>> # List all providers
        >>> providers = registry.list_providers()
        >>> 
        >>> # Get a model
        >>> model = registry.get_model("gpt-4", "openai")
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the provider registry.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._providers: Dict[str, "BaseProvider"] = {}
        self._models: Dict[str, "AIModel"] = {}
        self._model_index: Dict[str, Dict[str, "AIModel"]] = {}  # provider -> {model_id -> model}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> [model_id]
        self._status = RegistryStatus.UNINITIALIZED
        self._metrics = RegistryMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ProviderRegistry initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def status(self) -> RegistryStatus:
        """Get the registry status."""
        return self._status

    @property
    def metrics(self) -> RegistryMetrics:
        """Get the registry metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the registry is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the registry is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the provider registry.
        
        This method initializes all registered providers.
        """
        if self._initialized:
            logger.warning("ProviderRegistry already initialized")
            return
        
        logger.info("Initializing ProviderRegistry...")
        
        try:
            self._status = RegistryStatus.READY
            
            # Initialize all providers
            for provider_name, provider in self._providers.items():
                try:
                    await provider.initialize()
                    self._metrics.providers_initialized += 1
                    logger.info(f"Provider initialized: {provider_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize provider {provider_name}: {e}")
                    self._metrics.errors += 1
                    self._metrics.last_error = str(e)
                    self._metrics.last_error_time = datetime.utcnow()
            
            # Build indexes
            self._build_indexes()
            
            # Mark as initialized
            self._initialized = True
            
            logger.info("ProviderRegistry initialized successfully")
            
        except Exception as e:
            self._status = RegistryStatus.ERROR
            logger.error(f"Failed to initialize ProviderRegistry: {e}")
            raise

    async def start(self) -> None:
        """
        Start the provider registry.
        
        This method starts all registered providers.
        """
        if self._started:
            logger.warning("ProviderRegistry already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ProviderRegistry...")
        
        try:
            # Start all providers
            for provider_name, provider in self._providers.items():
                try:
                    await provider.start()
                    self._metrics.providers_started += 1
                    logger.info(f"Provider started: {provider_name}")
                except Exception as e:
                    logger.error(f"Failed to start provider {provider_name}: {e}")
                    self._metrics.errors += 1
                    self._metrics.last_error = str(e)
                    self._metrics.last_error_time = datetime.utcnow()
            
            # Mark as started
            self._started = True
            
            logger.info("ProviderRegistry started successfully")
            
        except Exception as e:
            self._status = RegistryStatus.ERROR
            logger.error(f"Failed to start ProviderRegistry: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the provider registry.
        
        This method stops all registered providers.
        """
        if not self._started:
            logger.warning("ProviderRegistry not started")
            return
        
        logger.info("Stopping ProviderRegistry...")
        
        try:
            # Stop all providers in reverse order
            for provider_name, provider in reversed(list(self._providers.items())):
                try:
                    await provider.stop()
                    logger.info(f"Provider stopped: {provider_name}")
                except Exception as e:
                    logger.error(f"Failed to stop provider {provider_name}: {e}")
                    self._metrics.errors += 1
                    self._metrics.last_error = str(e)
                    self._metrics.last_error_time = datetime.utcnow()
            
            # Mark as stopped
            self._started = False
            
            logger.info("ProviderRegistry stopped successfully")
            
        except Exception as e:
            self._status = RegistryStatus.ERROR
            logger.error(f"Failed to stop ProviderRegistry: {e}")
            raise

    def _build_indexes(self) -> None:
        """Build indexes for fast lookup."""
        self._models = {}
        self._model_index = {}
        self._capability_index = {}
        
        for provider_name, provider in self._providers.items():
            # Index models by provider
            self._model_index[provider_name] = {}
            
            for model in provider.models:
                # Add to global model index
                self._models[model.model_id] = model
                
                # Add to provider-specific index
                self._model_index[provider_name][model.model_id] = model
                
                # Index by capabilities
                for capability in ["chat", "completion", "embedding", "vision", "audio", "image", "video", "tool_calling", "structured_output", "streaming", "batch", "reasoning"]:
                    if model.has_capability(capability):
                        if capability not in self._capability_index:
                            self._capability_index[capability] = []
                        if model.model_id not in self._capability_index[capability]:
                            self._capability_index[capability].append(model.model_id)
        
        self._metrics.models_available = len(self._models)

    async def register_provider(self, provider: "BaseProvider") -> None:
        """
        Register a provider.
        
        Args:
            provider: Provider instance to register.
        
        Raises:
            ValueError: If provider is already registered.
        """
        async with self._lock:
            if provider.name in self._providers:
                raise ValueError(f"Provider already registered: {provider.name}")
            
            self._providers[provider.name] = provider
            self._metrics.providers_registered += 1
            
            # Rebuild indexes
            self._build_indexes()
            
            logger.info(f"Provider registered: {provider.name}")

    async def unregister_provider(self, provider_name: str) -> bool:
        """
        Unregister a provider.
        
        Args:
            provider_name: Name of the provider to unregister.
        
        Returns:
            True if provider was unregistered, False if not found.
        """
        async with self._lock:
            if provider_name not in self._providers:
                return False
            
            # Stop the provider if started
            provider = self._providers[provider_name]
            if provider.is_started:
                try:
                    await provider.stop()
                except Exception as e:
                    logger.error(f"Failed to stop provider {provider_name}: {e}")
            
            # Remove from registry
            del self._providers[provider_name]
            self._metrics.providers_registered -= 1
            self._metrics.providers_initialized -= 1
            self._metrics.providers_started -= 1
            
            # Rebuild indexes
            self._build_indexes()
            
            logger.info(f"Provider unregistered: {provider_name}")
            return True

    def get_provider(self, provider_name: str) -> Optional["BaseProvider"]:
        """
        Get a provider by name.
        
        Args:
            provider_name: Name of the provider to get.
        
        Returns:
            Provider instance or None if not found.
        """
        return self._providers.get(provider_name)

    def list_providers(self) -> List[str]:
        """
        List all registered provider names.
        
        Returns:
            List of provider names.
        """
        return list(self._providers.keys())

    def get_model(self, model_id: str, provider_name: Optional[str] = None) -> Optional["AIModel"]:
        """
        Get a model by ID.
        
        Args:
            model_id: ID of the model to get.
            provider_name: Optional provider name to filter by.
        
        Returns:
            AIModel instance or None if not found.
        """
        if provider_name:
            if provider_name in self._model_index:
                return self._model_index[provider_name].get(model_id)
            return None
        
        return self._models.get(model_id)

    def list_models(self, provider_name: Optional[str] = None) -> List["AIModel"]:
        """
        List all available models.
        
        Args:
            provider_name: Optional provider name to filter by.
        
        Returns:
            List of AIModel instances.
        """
        if provider_name:
            if provider_name in self._model_index:
                return list(self._model_index[provider_name].values())
            return []
        
        return list(self._models.values())

    def get_models_by_capability(self, capability: str) -> List["AIModel"]:
        """
        Get models that support a specific capability.
        
        Args:
            capability: Capability to filter by.
        
        Returns:
            List of AIModel instances.
        """
        model_ids = self._capability_index.get(capability, [])
        return [self._models[mid] for mid in model_ids if mid in self._models]

    def get_models_by_modality(self, modality: str) -> List["AIModel"]:
        """
        Get models that support a specific modality.
        
        Args:
            modality: Modality to filter by.
        
        Returns:
            List of AIModel instances.
        """
        from tangku_agentos.ai_foundation.models.model import ModelModality
        
        try:
            model_modality = ModelModality(modality)
        except ValueError:
            return []
        
        models = []
        for model in self._models.values():
            if model.has_modality(model_modality):
                models.append(model)
        return models

    async def route_request(self, request: Any) -> Tuple[Optional["BaseProvider"], Optional["AIModel"]]:
        """
        Route a request to the appropriate provider and model.
        
        Args:
            request: AIRequest to route.
        
        Returns:
            Tuple of (provider, model) or (None, None) if no match.
        """
        self._metrics.requests_routed += 1
        
        # If provider and model are specified, use them directly
        if request.provider and request.model:
            provider = self.get_provider(request.provider)
            if provider:
                model = await provider.get_model(request.model)
                if model:
                    return provider, model
            return None, None
        
        # If only model is specified, find the provider that has it
        if request.model:
            for provider_name, provider in self._providers.items():
                model = await provider.get_model(request.model)
                if model:
                    return provider, model
            return None, None
        
        # If only provider is specified, use its default model
        if request.provider:
            provider = self.get_provider(request.provider)
            if provider and provider.models:
                return provider, provider.models[0]
            return None, None
        
        # Find a provider that can handle the request
        for provider_name, provider in self._providers.items():
            for model in provider.models:
                if model.can_handle(request):
                    return provider, model
        
        # No match found
        return None, None

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the provider registry.
        
        Returns:
            Dictionary with registry information.
        """
        providers_info = {}
        for provider_name, provider in self._providers.items():
            providers_info[provider_name] = await provider.get_info()
        
        return {
            "status": self._status.value,
            "providers": providers_info,
            "models": {mid: model.to_dict() for mid, model in self._models.items()},
            "capabilities": {cap: model_ids for cap, model_ids in self._capability_index.items()},
            "metrics": self._metrics.to_dict(),
        }

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of all providers.
        
        Returns:
            Dictionary with health status for each provider.
        """
        health = {}
        for provider_name, provider in self._providers.items():
            try:
                health[provider_name] = await provider.check_health()
            except Exception as e:
                health[provider_name] = "error"
                logger.error(f"Health check failed for provider {provider_name}: {e}")
        return health

    async def reset(self) -> None:
        """
        Reset the provider registry.
        
        This method resets all providers and clears all state.
        """
        logger.info("Resetting ProviderRegistry...")
        
        try:
            # Reset all providers
            for provider_name, provider in self._providers.items():
                try:
                    await provider.reset()
                except Exception as e:
                    logger.error(f"Failed to reset provider {provider_name}: {e}")
            
            # Clear registry
            self._providers.clear()
            self._models.clear()
            self._model_index.clear()
            self._capability_index.clear()
            
            # Reset metrics
            self._metrics = RegistryMetrics()
            
            # Reset state
            self._status = RegistryStatus.UNINITIALIZED
            self._initialized = False
            self._started = False
            
            logger.info("ProviderRegistry reset successfully")
            
        except Exception as e:
            self._status = RegistryStatus.ERROR
            logger.error(f"Failed to reset ProviderRegistry: {e}")
            raise

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ProviderRegistry("
            f"status={self._status.value}, "
            f"providers={len(self._providers)}, "
            f"models={len(self._models)})"
        )
