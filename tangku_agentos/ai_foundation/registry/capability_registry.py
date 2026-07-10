"""
AI Foundation Framework - Capability Registry

This module provides the CapabilityRegistry class for managing model capabilities.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.model import AIModel, ModelCapability
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class CapabilityInfo:
    """
    Information about a capability.
    
    Attributes:
        capability: Name of the capability.
        description: Description of the capability.
        models: Set of model IDs that support this capability.
        providers: Set of provider names that support this capability.
        usage_count: Number of times this capability has been used.
        last_used: When the capability was last used.
    """

    capability: str
    description: str = ""
    models: Set[str] = field(default_factory=set)
    providers: Set[str] = field(default_factory=set)
    usage_count: int = 0
    last_used: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "capability": self.capability,
            "description": self.description,
            "models": list(self.models),
            "providers": list(self.providers),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


@dataclass
class CapabilityRegistryMetrics:
    """Metrics for the capability registry."""
    capabilities_registered: int = 0
    capability_checks: int = 0
    capability_matches: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "capabilities_registered": self.capabilities_registered,
            "capability_checks": self.capability_checks,
            "capability_matches": self.capability_matches,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class CapabilityRegistry:
    """
    Registry for managing model capabilities.
    
    This class provides a centralized way to track and query the capabilities
    of all registered models. It enables efficient capability-based model
    selection and discovery.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import CapabilityRegistry
        >>> 
        >>> # Create registry
        >>> registry = CapabilityRegistry()
        >>> 
        >>> # Check if a model has a capability
        >>> has_cap = await registry.has_capability("gpt-4", "tool_calling")
        >>> 
        >>> # Get models with a capability
        >>> models = await registry.get_models_with_capability("streaming")
        >>> 
        >>> # List all capabilities
        >>> capabilities = registry.list_capabilities()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the capability registry.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._capabilities: Dict[str, CapabilityInfo] = {}
        self._model_capabilities: Dict[str, Set[str]] = {}  # model_id -> set of capabilities
        self._metrics = CapabilityRegistryMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        # Define known capabilities
        self._known_capabilities = {
            "chat": "Supports chat/conversation interactions",
            "completion": "Supports text completion",
            "embedding": "Supports generating embeddings",
            "vision": "Supports processing images/vision",
            "audio": "Supports processing audio",
            "image": "Supports generating images",
            "video": "Supports processing video",
            "tool_calling": "Supports calling tools/functions",
            "structured_output": "Supports generating structured output",
            "streaming": "Supports streaming responses",
            "batch": "Supports batch processing",
            "reasoning": "Supports advanced reasoning",
        }
        
        logger.info("CapabilityRegistry initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> CapabilityRegistryMetrics:
        """Get the capability registry metrics."""
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
        Initialize the capability registry.
        
        This method loads capabilities from all registered models.
        """
        if self._initialized:
            logger.warning("CapabilityRegistry already initialized")
            return
        
        logger.info("Initializing CapabilityRegistry...")
        
        # Initialize known capabilities
        await self._initialize_known_capabilities()
        
        # Load capabilities from all models
        await self._load_from_models()
        
        self._initialized = True
        logger.info("CapabilityRegistry initialized successfully")

    async def start(self) -> None:
        """
        Start the capability registry.
        """
        if self._started:
            logger.warning("CapabilityRegistry already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting CapabilityRegistry...")
        
        self._started = True
        logger.info("CapabilityRegistry started successfully")

    async def stop(self) -> None:
        """
        Stop the capability registry.
        """
        if not self._started:
            logger.warning("CapabilityRegistry not started")
            return
        
        logger.info("Stopping CapabilityRegistry...")
        
        self._started = False
        logger.info("CapabilityRegistry stopped successfully")

    async def _initialize_known_capabilities(self) -> None:
        """Initialize known capabilities."""
        for capability, description in self._known_capabilities.items():
            self._capabilities[capability] = CapabilityInfo(
                capability=capability,
                description=description,
            )
            self._metrics.capabilities_registered += 1

    async def _load_from_models(self) -> None:
        """Load capabilities from all registered models."""
        models = await self._foundation.models.list_models()
        
        for model in models:
            await self.register_model_capabilities(model)

    async def register_model_capabilities(self, model: "AIModel") -> None:
        """
        Register the capabilities of a model.
        
        Args:
            model: AIModel to register capabilities for.
        """
        async with self._lock:
            # Track capabilities for this model
            model_capabilities = set()
            
            # Add capabilities from the model's capability object
            if model.capabilities.supports_chat:
                model_capabilities.add("chat")
            if model.capabilities.supports_completion:
                model_capabilities.add("completion")
            if model.capabilities.supports_embedding:
                model_capabilities.add("embedding")
            if model.capabilities.supports_vision:
                model_capabilities.add("vision")
            if model.capabilities.supports_audio:
                model_capabilities.add("audio")
            if model.capabilities.supports_image_generation:
                model_capabilities.add("image")
            if model.capabilities.supports_video:
                model_capabilities.add("video")
            if model.capabilities.supports_tool_calling:
                model_capabilities.add("tool_calling")
            if model.capabilities.supports_structured_output:
                model_capabilities.add("structured_output")
            if model.capabilities.supports_streaming:
                model_capabilities.add("streaming")
            if model.capabilities.supports_batch:
                model_capabilities.add("batch")
            if model.capabilities.supports_reasoning:
                model_capabilities.add("reasoning")
            
            # Add capabilities from modalities
            for modality in model.modalities:
                modality_str = modality.value
                if modality_str not in model_capabilities:
                    model_capabilities.add(modality_str)
            
            # Store model capabilities
            self._model_capabilities[model.model_id] = model_capabilities
            
            # Update capability info
            for capability in model_capabilities:
                if capability not in self._capabilities:
                    self._capabilities[capability] = CapabilityInfo(
                        capability=capability,
                        description=self._known_capabilities.get(capability, ""),
                    )
                    self._metrics.capabilities_registered += 1
                
                # Add model to capability
                self._capabilities[capability].models.add(model.model_id)
                self._capabilities[capability].providers.add(model.provider)

    async def has_capability(self, model_id: str, capability: str) -> bool:
        """
        Check if a model has a specific capability.
        
        Args:
            model_id: ID of the model to check.
            capability: Capability to check for.
        
        Returns:
            True if the model has the capability, False otherwise.
        """
        self._metrics.capability_checks += 1
        
        # Check model capabilities
        model_caps = self._model_capabilities.get(model_id, set())
        if capability in model_caps:
            self._metrics.capability_matches += 1
            return True
        
        # Check if model exists and has the capability
        model = await self._foundation.models.get_model(model_id)
        if model and model.has_capability(capability):
            self._metrics.capability_matches += 1
            return True
        
        return False

    async def get_model_capabilities(self, model_id: str) -> Set[str]:
        """
        Get all capabilities of a model.
        
        Args:
            model_id: ID of the model.
        
        Returns:
            Set of capability names.
        """
        # Get from cache
        model_caps = self._model_capabilities.get(model_id, set())
        if model_caps:
            return model_caps
        
        # Get from model
        model = await self._foundation.models.get_model(model_id)
        if model:
            capabilities = set()
            
            # Add capabilities from the model's capability object
            if model.capabilities.supports_chat:
                capabilities.add("chat")
            if model.capabilities.supports_completion:
                capabilities.add("completion")
            if model.capabilities.supports_embedding:
                capabilities.add("embedding")
            if model.capabilities.supports_vision:
                capabilities.add("vision")
            if model.capabilities.supports_audio:
                capabilities.add("audio")
            if model.capabilities.supports_image_generation:
                capabilities.add("image")
            if model.capabilities.supports_video:
                capabilities.add("video")
            if model.capabilities.supports_tool_calling:
                capabilities.add("tool_calling")
            if model.capabilities.supports_structured_output:
                capabilities.add("structured_output")
            if model.capabilities.supports_streaming:
                capabilities.add("streaming")
            if model.capabilities.supports_batch:
                capabilities.add("batch")
            if model.capabilities.supports_reasoning:
                capabilities.add("reasoning")
            
            # Add capabilities from modalities
            for modality in model.modalities:
                capabilities.add(modality.value)
            
            # Cache the capabilities
            self._model_capabilities[model_id] = capabilities
            
            return capabilities
        
        return set()

    async def get_models_with_capability(self, capability: str) -> List[str]:
        """
        Get all model IDs that have a specific capability.
        
        Args:
            capability: Capability to filter by.
        
        Returns:
            List of model IDs.
        """
        cap_info = self._capabilities.get(capability)
        if cap_info:
            return list(cap_info.models)
        return []

    async def get_providers_with_capability(self, capability: str) -> List[str]:
        """
        Get all provider names that have models with a specific capability.
        
        Args:
            capability: Capability to filter by.
        
        Returns:
            List of provider names.
        """
        cap_info = self._capabilities.get(capability)
        if cap_info:
            return list(cap_info.providers)
        return []

    async def list_capabilities(self) -> List[str]:
        """
        List all registered capabilities.
        
        Returns:
            List of capability names.
        """
        return list(self._capabilities.keys())

    async def get_capability_info(self, capability: str) -> Optional[CapabilityInfo]:
        """
        Get information about a specific capability.
        
        Args:
            capability: Name of the capability.
        
        Returns:
            CapabilityInfo or None if not found.
        """
        return self._capabilities.get(capability)

    async def find_models_by_capabilities(
        self,
        required_capabilities: List[str],
        optional_capabilities: List[str] = None,
    ) -> List[str]:
        """
        Find models that have all required capabilities and optionally some optional ones.
        
        Args:
            required_capabilities: List of capabilities that must be present.
            optional_capabilities: List of capabilities that are nice to have.
        
        Returns:
            List of model IDs that match the criteria.
        """
        matching_models = set()
        
        # Find models with all required capabilities
        for capability in required_capabilities:
            models = await self.get_models_with_capability(capability)
            if not matching_models:
                matching_models.update(models)
            else:
                matching_models.intersection_update(models)
        
        # If no models match all required capabilities, return empty
        if not matching_models:
            return []
        
        # If optional capabilities are specified, prioritize models with them
        if optional_capabilities:
            # Score models by number of optional capabilities they have
            model_scores = {}
            for model_id in matching_models:
                model_caps = await self.get_model_capabilities(model_id)
                score = sum(1 for cap in optional_capabilities if cap in model_caps)
                model_scores[model_id] = score
            
            # Sort by score (descending) and return
            sorted_models = sorted(
                matching_models,
                key=lambda mid: model_scores.get(mid, 0),
                reverse=True
            )
            return sorted_models
        
        return list(matching_models)

    async def record_capability_usage(self, model_id: str, capability: str) -> None:
        """
        Record that a capability was used.
        
        Args:
            model_id: ID of the model that used the capability.
            capability: Capability that was used.
        """
        cap_info = self._capabilities.get(capability)
        if cap_info:
            cap_info.usage_count += 1
            cap_info.last_used = datetime.utcnow()

    async def get_capability_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all capabilities.
        
        Returns:
            Dictionary with capability statistics.
        """
        stats = {}
        for capability, info in self._capabilities.items():
            stats[capability] = {
                "description": info.description,
                "model_count": len(info.models),
                "provider_count": len(info.providers),
                "usage_count": info.usage_count,
                "last_used": info.last_used.isoformat() if info.last_used else None,
            }
        return stats

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the capability registry.
        
        Returns:
            Dictionary with capability registry information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "capabilities": len(self._capabilities),
            "models": len(self._model_capabilities),
            "metrics": self._metrics.to_dict(),
        }

    async def refresh(self) -> None:
        """
        Refresh the capability registry by reloading from models.
        """
        logger.info("Refreshing CapabilityRegistry...")
        
        async with self._lock:
            self._capabilities.clear()
            self._model_capabilities.clear()
            
            # Reload from models
            await self._initialize_known_capabilities()
            await self._load_from_models()
        
        logger.info("CapabilityRegistry refreshed successfully")

    async def reset(self) -> None:
        """
        Reset the capability registry.
        
        This method clears all capabilities and resets all state.
        """
        logger.info("Resetting CapabilityRegistry...")
        
        async with self._lock:
            self._capabilities.clear()
            self._model_capabilities.clear()
            self._metrics = CapabilityRegistryMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("CapabilityRegistry reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CapabilityRegistry("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"capabilities={len(self._capabilities)})"
        )
