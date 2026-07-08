"""
TangkuAgentOS Provider Runtime - Provider Factory

This module implements a factory for creating and managing provider instances.
It supports:
- Lazy loading of providers
- Singleton pattern for provider instances
- Dependency injection
- Connection pooling
- Caching and reuse of provider instances
- Thread-safe and async-safe operations

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import importlib
import logging
from functools import lru_cache
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .interfaces import (
        BaseProvider,
        ProviderID,
        ProviderAdapter,
        ModelConfiguration,
        ProviderSettings,
    )


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================

T = TypeVar("T", bound="BaseProvider")
ProviderClass = Type[Any]
ProviderFactoryFunc = Callable[..., Any]


# =============================================================================
# Exceptions
# =============================================================================

class FactoryError(Exception):
    """Base exception for factory-related errors."""

    pass


class ProviderCreationError(FactoryError):
    """Raised when a provider cannot be created."""

    pass


class ProviderNotSupportedError(FactoryError):
    """Raised when a provider is not supported."""

    pass


# =============================================================================
# Provider Factory
# =============================================================================

class ProviderFactory:
    """
    Factory for creating and managing provider instances.

    Features:
    - Lazy loading of providers
    - Singleton pattern for provider instances
    - Dependency injection
    - Connection pooling
    - Caching and reuse of provider instances
    - Thread-safe and async-safe operations

    Example:
        factory = ProviderFactory()
        provider = await factory.create("openai", api_key="sk-...")
        # Reuse the same instance
        same_provider = await factory.create("openai")
    """

    def __init__(
        self,
        registry: Optional[Any] = None,
        max_pool_size: int = 10,
    ):
        """
        Initialize the provider factory.

        Args:
            registry: Provider registry instance. If None, uses the global registry.
            max_pool_size: Maximum number of provider instances to keep in the pool.
        """
        from .registry import get_registry

        self._registry = registry or get_registry()
        self._instances: Dict[str, Any] = {}
        self._pool: Dict[str, List[Any]] = {}
        self._lock = RLock()
        self._async_lock = asyncio.Lock()
        self._max_pool_size = max_pool_size
        self._builtin_providers: Dict[str, ProviderClass] = {}

    def register_builtin_provider(
        self,
        provider_id: str,
        provider_class: ProviderClass,
    ) -> None:
        """
        Register a built-in provider class.

        Args:
            provider_id: Unique identifier for the provider.
            provider_class: Provider class.
        """
        with self._lock:
            self._builtin_providers[provider_id] = provider_class

    def _lazy_load_builtin(self, provider_id: str) -> ProviderClass:
        """
        Lazy-load a built-in provider class.

        Args:
            provider_id: Unique identifier for the provider.

        Returns:
            ProviderClass: Provider class.

        Raises:
            ProviderNotSupportedError: If the provider is not supported.
        """
        # Import built-in providers dynamically to avoid circular imports
        provider_map = {
            "openai": "OpenAIProvider",
            "anthropic": "AnthropicProvider",
            "google": "GoogleProvider",
            "mistral": "MistralProvider",
            "groq": "GroqProvider",
            "openrouter": "OpenRouterProvider",
            "ollama": "OllamaProvider",
            "together": "TogetherProvider",
            "cohere": "CohereProvider",
            "xai": "XAIProvider",
            "deepseek": "DeepSeekProvider",
            "fireworks": "FireworksProvider",
            "cerebras": "CerebrasProvider",
            "huggingface": "HuggingFaceProvider",
            "azure_openai": "AzureOpenAIProvider",
            "aws_bedrock": "AWSBedrockProvider",
            "vertex_ai": "VertexAIProvider",
        }

        if provider_id not in provider_map:
            raise ProviderNotSupportedError(
                f"Provider {provider_id!r} is not a built-in provider."
            )

        # Dynamically import the provider class
        try:
            module = importlib.import_module(
                f"tangku_agentos.provider_runtime.providers.{provider_id}"
            )
            provider_class = getattr(module, provider_map[provider_id])
            self._builtin_providers[provider_id] = provider_class
            return provider_class
        except ImportError as e:
            raise ProviderNotSupportedError(
                f"Failed to import provider {provider_id!r}: {e}"
            )
        except AttributeError as e:
            raise ProviderNotSupportedError(
                f"Provider {provider_id!r} does not have a valid class: {e}"
            )

    async def create(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Create or retrieve a provider instance.

        Args:
            provider_id: Unique identifier for the provider.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Any: Provider instance.

        Raises:
            ProviderCreationError: If the provider cannot be created.
            ProviderNotSupportedError: If the provider is not supported.
        """
        async with self._async_lock:
            # Check if instance already exists
            if provider_id in self._instances:
                logger.debug(f"Reusing existing provider instance: {provider_id}")
                return self._instances[provider_id]

            # Try to get the provider class from the registry
            try:
                provider_class = self._registry.get_provider_class(provider_id)
            except Exception:
                # Fall back to built-in providers
                if provider_id in self._builtin_providers:
                    provider_class = self._builtin_providers[provider_id]
                else:
                    try:
                        provider_class = self._lazy_load_builtin(provider_id)
                    except ProviderNotSupportedError:
                        raise ProviderNotSupportedError(
                            f"Provider {provider_id!r} is not registered or supported."
                        )

            # Create new instance
            try:
                logger.debug(f"Creating new provider instance: {provider_id}")
                instance = provider_class(**kwargs)
                if hasattr(instance, "initialize"):
                    if asyncio.iscoroutinefunction(instance.initialize):
                        await instance.initialize()
                    else:
                        instance.initialize()
                self._instances[provider_id] = instance
                return instance
            except Exception as e:
                logger.error(f"Failed to create provider {provider_id}: {e}")
                raise ProviderCreationError(
                    f"Failed to create provider {provider_id}: {e}"
                ) from e

    async def get(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Get a provider instance (alias for create).

        Args:
            provider_id: Unique identifier for the provider.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Any: Provider instance.
        """
        return await self.create(provider_id, **kwargs)

    async def destroy(self, provider_id: str) -> None:
        """
        Destroy a provider instance.

        Args:
            provider_id: Unique identifier for the provider.
        """
        async with self._async_lock:
            if provider_id in self._instances:
                try:
                    if hasattr(self._instances[provider_id], "close"):
                        if asyncio.iscoroutinefunction(
                            self._instances[provider_id].close
                        ):
                            await self._instances[provider_id].close()
                        else:
                            self._instances[provider_id].close()
                except Exception as e:
                    logger.warning(f"Error closing provider {provider_id}: {e}")
                del self._instances[provider_id]
                logger.debug(f"Destroyed provider instance: {provider_id}")

    async def destroy_all(self) -> None:
        """Destroy all provider instances."""
        async with self._async_lock:
            for provider_id in list(self._instances.keys()):
                await self.destroy(provider_id)
            self._instances.clear()
            logger.debug("Destroyed all provider instances")

    def clear(self) -> None:
        """Clear all cached instances (non-async version for sync contexts)."""
        with self._lock:
            for instance in self._instances.values():
                try:
                    if hasattr(instance, "close"):
                        instance.close()
                except Exception:
                    pass
            self._instances.clear()

    @property
    def instances(self) -> Dict[str, Any]:
        """Get a copy of the current instances."""
        with self._lock:
            return self._instances.copy()

    @property
    def supported_providers(self) -> List[str]:
        """Get a list of supported provider IDs."""
        with self._lock:
            supported = list(self._builtin_providers.keys())
            try:
                supported.extend(self._registry.list_providers())
            except Exception:
                pass
            return supported


# =============================================================================
# Provider Pool for Connection Pooling
# =============================================================================

class ProviderPool:
    """
    Pool of provider instances for connection reuse.

    Features:
    - Maintains a pool of initialized provider instances
    - Reuses instances to avoid repeated initialization
    - Supports max pool size
    - Thread-safe and async-safe operations

    Example:
        pool = ProviderPool(max_size=5)
        provider = await pool.acquire("openai")
        # Use provider...
        await pool.release(provider)
    """

    def __init__(self, max_size: int = 10):
        """
        Initialize the provider pool.

        Args:
            max_size: Maximum number of provider instances to keep in the pool.
        """
        self._pool: Dict[str, List[Any]] = {}
        self._max_size = max_size
        self._lock = RLock()
        self._async_lock = asyncio.Lock()

    async def acquire(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Acquire a provider instance from the pool.

        Args:
            provider_id: Unique identifier for the provider.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Any: Provider instance.
        """
        async with self._async_lock:
            if provider_id not in self._pool:
                self._pool[provider_id] = []

            # Reuse existing instance if available
            if self._pool[provider_id]:
                instance = self._pool[provider_id].pop()
                logger.debug(f"Reusing provider instance from pool: {provider_id}")
                return instance

            # Create new instance if pool is empty
            factory = ProviderFactory()
            instance = await factory.create(provider_id, **kwargs)
            return instance

    async def release(self, instance: Any) -> None:
        """
        Release a provider instance back to the pool.

        Args:
            instance: Provider instance to release.
        """
        if not hasattr(instance, "provider_id"):
            logger.warning("Released instance has no provider_id attribute")
            return

        provider_id = instance.provider_id
        async with self._async_lock:
            if provider_id not in self._pool:
                self._pool[provider_id] = []

            if len(self._pool[provider_id]) < self._max_size:
                self._pool[provider_id].append(instance)
                logger.debug(f"Released provider instance to pool: {provider_id}")
            else:
                # Pool is full, close the instance
                try:
                    if hasattr(instance, "close"):
                        if asyncio.iscoroutinefunction(instance.close):
                            await instance.close()
                        else:
                            instance.close()
                except Exception as e:
                    logger.warning(f"Error closing provider {provider_id}: {e}")

    async def clear(self) -> None:
        """Clear all instances in the pool."""
        async with self._async_lock:
            for provider_id in list(self._pool.keys()):
                for instance in self._pool[provider_id]:
                    try:
                        if hasattr(instance, "close"):
                            if asyncio.iscoroutinefunction(instance.close):
                                await instance.close()
                            else:
                                instance.close()
                    except Exception as e:
                        logger.warning(f"Error closing provider {provider_id}: {e}")
                self._pool[provider_id].clear()
            self._pool.clear()
            logger.debug("Cleared provider pool")

    @property
    def pool_size(self) -> int:
        """Get the total number of instances in the pool."""
        with self._lock:
            return sum(len(instances) for instances in self._pool.values())


# =============================================================================
# Dependency Injection Helpers
# =============================================================================

class ProviderInjector:
    """
    Helper class for dependency injection of providers.

    Features:
    - Inject provider instances into target objects
    - Support for both sync and async initialization
    - Thread-safe and async-safe operations

    Example:
        injector = ProviderInjector()
        provider = await injector.get_provider("openai")
        # Or inject into a target object
        await injector.inject(target, "openai", attr_name="provider")
    """

    def __init__(self, factory: Optional[ProviderFactory] = None):
        """
        Initialize the provider injector.

        Args:
            factory: Provider factory instance. If None, creates a new one.
        """
        self._factory = factory or ProviderFactory()

    async def get_provider(
        self,
        provider_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Get a provider instance with dependency injection.

        Args:
            provider_id: Unique identifier for the provider.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            Any: Provider instance.
        """
        return await self._factory.get(provider_id, **kwargs)

    async def inject(
        self,
        target: Any,
        provider_id: str,
        attr_name: str = "provider",
        **kwargs: Any,
    ) -> None:
        """
        Inject a provider instance into a target object.

        Args:
            target: Object to inject the provider into.
            provider_id: Unique identifier for the provider.
            attr_name: Name of the attribute to set on the target.
            **kwargs: Additional arguments to pass to the provider constructor.
        """
        provider = await self.get_provider(provider_id, **kwargs)
        setattr(target, attr_name, provider)


# =============================================================================
# Decorator for Lazy Provider Loading
# =============================================================================

def lazy_provider(
    provider_id: str,
    **kwargs: Any,
):
    """
    Decorator to lazily load a provider instance as a property.

    Usage:
        class MyService:
            @lazy_provider("openai")
            def openai(self) -> Any:
                ...

    The decorated property will return the same provider instance on each access.

    Args:
        provider_id: Unique identifier for the provider.
        **kwargs: Additional arguments to pass to the provider constructor.

    Returns:
        Callable: Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @property
        @lru_cache(maxsize=1)
        def wrapper(self) -> Any:
            factory = ProviderFactory()
            return asyncio.run(factory.create(provider_id, **kwargs))

        return wrapper

    return decorator


# =============================================================================
# Singleton Factory Instance
# =============================================================================

_factory: Optional[ProviderFactory] = None


def get_factory() -> ProviderFactory:
    """
    Get the global provider factory instance.

    Returns:
        ProviderFactory: Global factory instance.
    """
    global _factory
    if _factory is None:
        _factory = ProviderFactory()
    return _factory


def reset_factory() -> None:
    """
    Reset the global provider factory (useful for testing).
    """
    global _factory
    if _factory is not None:
        asyncio.run(_factory.destroy_all())
    _factory = None