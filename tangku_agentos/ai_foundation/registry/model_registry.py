"""
AI Foundation Framework - Model Registry

This module provides the ModelRegistry class for managing AI models.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.model import AIModel
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class ModelRegistryMetrics:
    """Metrics for the model registry."""
    models_registered: int = 0
    models_available: int = 0
    models_used: int = 0
    lookups: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "models_registered": self.models_registered,
            "models_available": self.models_available,
            "models_used": self.models_used,
            "lookups": self.lookups,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ModelRegistry:
    """
    Registry for managing AI models.
    
    This class provides a centralized way to register, manage, and discover
    AI models. It maintains a comprehensive catalog of all available models
    across all providers.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ModelRegistry
        >>> 
        >>> # Create registry
        >>> registry = ModelRegistry()
        >>> 
        >>> # Register a model
        >>> await registry.register_model(model)
        >>> 
        >>> # Get a model
        >>> model = registry.get_model("gpt-4")
        >>> 
        >>> # List all models
        >>> models = registry.list_models()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the model registry.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._models: Dict[str, "AIModel"] = {}
        self._provider_index: Dict[str, Set[str]] = {}  # provider -> set of model_ids
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> set of model_ids
        self._modality_index: Dict[str, Set[str]] = {}  # modality -> set of model_ids
        self._type_index: Dict[str, Set[str]] = {}  # model_type -> set of model_ids
        self._name_index: Dict[str, str] = {}  # name -> model_id
        self._metrics = ModelRegistryMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ModelRegistry initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> ModelRegistryMetrics:
        """Get the model registry metrics."""
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
        Initialize the model registry.
        
        This method loads models from all registered providers.
        """
        if self._initialized:
            logger.warning("ModelRegistry already initialized")
            return
        
        logger.info("Initializing ModelRegistry...")
        
        # Load models from all providers
        await self._load_from_providers()
        
        self._initialized = True
        logger.info("ModelRegistry initialized successfully")

    async def start(self) -> None:
        """
        Start the model registry.
        """
        if self._started:
            logger.warning("ModelRegistry already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ModelRegistry...")
        
        self._started = True
        logger.info("ModelRegistry started successfully")

    async def stop(self) -> None:
        """
        Stop the model registry.
        """
        if not self._started:
            logger.warning("ModelRegistry not started")
            return
        
        logger.info("Stopping ModelRegistry...")
        
        self._started = False
        logger.info("ModelRegistry stopped successfully")

    async def _load_from_providers(self) -> None:
        """Load models from all registered providers."""
        providers = await self._foundation.providers.list_providers()
        
        for provider_name in providers:
            provider = self._foundation.providers.get_provider(provider_name)
            if provider:
                for model in provider.models:
                    await self.register_model(model)

    async def register_model(self, model: "AIModel") -> str:
        """
        Register a model.
        
        Args:
            model: AIModel to register.
        
        Returns:
            Model ID.
        
        Raises:
            ValueError: If model with same ID already exists.
        """
        async with self._lock:
            # Check if model with same ID already exists
            if model.model_id in self._models:
                # Update existing model
                existing = self._models[model.model_id]
                existing.name = model.name
                existing.provider = model.provider
                existing.model_type = model.model_type
                existing.modalities = model.modalities
                existing.capabilities = model.capabilities
                existing.limits = model.limits
                existing.pricing = model.pricing
                existing.status = model.status
                existing.version = model.version
                existing.description = model.description
                existing.metadata = model.metadata
                existing.updated_at = datetime.utcnow()
                
                return model.model_id
            
            # Register new model
            self._models[model.model_id] = model
            
            # Index by provider
            if model.provider not in self._provider_index:
                self._provider_index[model.provider] = set()
            self._provider_index[model.provider].add(model.model_id)
            
            # Index by capabilities
            for capability in ["chat", "completion", "embedding", "vision", "audio", "image", "video", "tool_calling", "structured_output", "streaming", "batch", "reasoning"]:
                if model.has_capability(capability):
                    if capability not in self._capability_index:
                        self._capability_index[capability] = set()
                    self._capability_index[capability].add(model.model_id)
            
            # Index by modalities
            for modality in model.modalities:
                modality_str = modality.value
                if modality_str not in self._modality_index:
                    self._modality_index[modality_str] = set()
                self._modality_index[modality_str].add(model.model_id)
            
            # Index by type
            type_str = model.model_type.value
            if type_str not in self._type_index:
                self._type_index[type_str] = set()
            self._type_index[type_str].add(model.model_id)
            
            # Index by name
            self._name_index[model.name] = model.model_id
            
            # Update metrics
            self._metrics.models_registered += 1
            if model.status == "available":
                self._metrics.models_available += 1
            
            logger.debug(f"Model registered: {model.model_id}")
            return model.model_id

    async def unregister_model(self, model_id: str) -> bool:
        """
        Unregister a model.
        
        Args:
            model_id: ID of the model to unregister.
        
        Returns:
            True if model was unregistered, False if not found.
        """
        async with self._lock:
            if model_id not in self._models:
                return False
            
            model = self._models[model_id]
            
            # Remove from provider index
            if model.provider in self._provider_index:
                self._provider_index[model.provider].discard(model_id)
                if not self._provider_index[model.provider]:
                    del self._provider_index[model.provider]
            
            # Remove from capability index
            for capability in ["chat", "completion", "embedding", "vision", "audio", "image", "video", "tool_calling", "structured_output", "streaming", "batch", "reasoning"]:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(model_id)
                    if not self._capability_index[capability]:
                        del self._capability_index[capability]
            
            # Remove from modality index
            for modality in model.modalities:
                modality_str = modality.value
                if modality_str in self._modality_index:
                    self._modality_index[modality_str].discard(model_id)
                    if not self._modality_index[modality_str]:
                        del self._modality_index[modality_str]
            
            # Remove from type index
            type_str = model.model_type.value
            if type_str in self._type_index:
                self._type_index[type_str].discard(model_id)
                if not self._type_index[type_str]:
                    del self._type_index[type_str]
            
            # Remove from name index
            if model.name in self._name_index:
                del self._name_index[model.name]
            
            # Remove from models
            del self._models[model_id]
            
            # Update metrics
            self._metrics.models_registered -= 1
            if model.status == "available":
                self._metrics.models_available -= 1
            
            logger.debug(f"Model unregistered: {model_id}")
            return True

    async def get_model(self, model_id: str) -> Optional["AIModel"]:
        """
        Get a model by ID.
        
        Args:
            model_id: ID of the model to get.
        
        Returns:
            AIModel or None if not found.
        """
        async with self._lock:
            self._metrics.lookups += 1
            return self._models.get(model_id)

    async def get_model_by_name(self, name: str) -> Optional["AIModel"]:
        """
        Get a model by name.
        
        Args:
            name: Name of the model to get.
        
        Returns:
            AIModel or None if not found.
        """
        async with self._lock:
            self._metrics.lookups += 1
            model_id = self._name_index.get(name)
            if model_id:
                return self._models.get(model_id)
            return None

    async def list_models(
        self,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        modality: Optional[str] = None,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List["AIModel"]:
        """
        List all models, optionally filtered.
        
        Args:
            provider: Optional provider to filter by.
            capability: Optional capability to filter by.
            modality: Optional modality to filter by.
            model_type: Optional model type to filter by.
            status: Optional model status to filter by.
        
        Returns:
            List of AIModel instances.
        """
        async with self._lock:
            models = []
            
            # Filter by provider
            if provider:
                model_ids = self._provider_index.get(provider, set())
            else:
                model_ids = set(self._models.keys())
            
            # Filter by capability
            if capability:
                cap_model_ids = self._capability_index.get(capability, set())
                model_ids.intersection_update(cap_model_ids)
            
            # Filter by modality
            if modality:
                mod_model_ids = self._modality_index.get(modality, set())
                model_ids.intersection_update(mod_model_ids)
            
            # Filter by type
            if model_type:
                type_model_ids = self._type_index.get(model_type, set())
                model_ids.intersection_update(type_model_ids)
            
            # Get models and filter by status
            for model_id in model_ids:
                model = self._models.get(model_id)
                if model:
                    if status and model.status.value != status:
                        continue
                    models.append(model)
            
            return models

    async def get_models_by_provider(self, provider: str) -> List["AIModel"]:
        """
        Get all models from a specific provider.
        
        Args:
            provider: Provider name.
        
        Returns:
            List of AIModel instances.
        """
        async with self._lock:
            model_ids = self._provider_index.get(provider, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def get_models_by_capability(self, capability: str) -> List["AIModel"]:
        """
        Get all models with a specific capability.
        
        Args:
            capability: Capability to filter by.
        
        Returns:
            List of AIModel instances.
        """
        async with self._lock:
            model_ids = self._capability_index.get(capability, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def get_models_by_modality(self, modality: str) -> List["AIModel"]:
        """
        Get all models with a specific modality.
        
        Args:
            modality: Modality to filter by.
        
        Returns:
            List of AIModel instances.
        """
        async with self._lock:
            model_ids = self._modality_index.get(modality, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def get_models_by_type(self, model_type: str) -> List["AIModel"]:
        """
        Get all models of a specific type.
        
        Args:
            model_type: Model type to filter by.
        
        Returns:
            List of AIModel instances.
        """
        async with self._lock:
            model_ids = self._type_index.get(model_type, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def find_models(
        self,
        query: str,
        limit: int = 10,
    ) -> List["AIModel"]:
        """
        Find models matching a query.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
        
        Returns:
            List of AIModel instances.
        """
        query_lower = query.lower()
        
        results = []
        for model in self._models.values():
            if (query_lower in model.model_id.lower() or
                query_lower in model.name.lower() or
                query_lower in model.description.lower()):
                results.append(model)
                if len(results) >= limit:
                    break
        
        return results

    async def get_available_models(self) -> List["AIModel"]:
        """
        Get all available models.
        
        Returns:
            List of AIModel instances.
        """
        return await self.list_models(status="available")

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the model registry.
        
        Returns:
            Dictionary with model registry information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "models": len(self._models),
            "providers": len(self._provider_index),
            "capabilities": len(self._capability_index),
            "modalities": len(self._modality_index),
            "types": len(self._type_index),
            "metrics": self._metrics.to_dict(),
        }

    async def refresh(self) -> None:
        """
        Refresh the model registry by reloading from providers.
        """
        logger.info("Refreshing ModelRegistry...")
        
        async with self._lock:
            # Clear existing models
            self._models.clear()
            self._provider_index.clear()
            self._capability_index.clear()
            self._modality_index.clear()
            self._type_index.clear()
            self._name_index.clear()
            
            # Reload from providers
            await self._load_from_providers()
        
        logger.info("ModelRegistry refreshed successfully")

    async def reset(self) -> None:
        """
        Reset the model registry.
        
        This method clears all models and resets all state.
        """
        logger.info("Resetting ModelRegistry...")
        
        async with self._lock:
            self._models.clear()
            self._provider_index.clear()
            self._capability_index.clear()
            self._modality_index.clear()
            self._type_index.clear()
            self._name_index.clear()
            self._metrics = ModelRegistryMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("ModelRegistry reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ModelRegistry("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"models={len(self._models)})"
        )
