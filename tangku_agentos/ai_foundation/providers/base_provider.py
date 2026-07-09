"""
Base Provider Interface for TangkuAgentOS AI Foundation Framework.

This module defines the universal provider interface that all AI providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Type
from ..models.base_model import AIModel, ModelCapabilities


class BaseProvider(ABC):
    """Abstract base class for all AI providers in TangkuAgentOS."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the provider (e.g., 'openai', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def api_key(self) -> Optional[str]:
        """API key for the provider (if applicable)."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> Optional[str]:
        """Base URL for the provider's API (if applicable)."""
        pass

    @abstractmethod
    def get_model_class(self) -> Type[AIModel]:
        """Return the model class associated with this provider."""
        pass

    @abstractmethod
    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the provider (e.g., authenticate, validate API key)."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List all available models for this provider."""
        pass

    @abstractmethod
    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific model."""
        pass

    @abstractmethod
    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of a model for this provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform a health check for the provider."""
        pass
