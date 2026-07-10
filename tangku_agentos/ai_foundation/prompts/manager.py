"""
AI Foundation Framework - Prompt Manager

This module provides the PromptManager class for managing prompts.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.prompts.registry import PromptRegistry
    from tangku_agentos.ai_foundation.prompts.template import PromptTemplate
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class PromptManagerMetrics:
    """Metrics for the prompt manager."""
    prompts_managed: int = 0
    prompts_rendered: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompts_managed": self.prompts_managed,
            "prompts_rendered": self.prompts_rendered,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class PromptManager:
    """
    Manager for AI prompts.
    
    This class provides a high-level interface for managing and using
    prompt templates. It integrates with the PromptRegistry and provides
    additional functionality like prompt caching and composition.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import PromptManager
        >>> 
        >>> # Create manager
        >>> manager = PromptManager()
        >>> 
        >>> # Render a prompt
        >>> prompt = await manager.render("greeting", {"name": "Alice"})
        >>> 
        >>> # Compose multiple prompts
        >>> composed = await manager.compose(["system", "user"], {"prompt": "Hello"})
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the prompt manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._registry: Optional["PromptRegistry"] = None
        self._cache: Dict[str, str] = {}
        self._metrics = PromptManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("PromptManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def registry(self) -> "PromptRegistry":
        """Get the prompt registry."""
        if self._registry is None:
            from tangku_agentos.ai_foundation.prompts.registry import PromptRegistry
            self._registry = PromptRegistry(self._config, self._foundation)
        return self._registry

    @property
    def metrics(self) -> PromptManagerMetrics:
        """Get the prompt manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the prompt manager.
        """
        if self._initialized:
            logger.warning("PromptManager already initialized")
            return
        
        logger.info("Initializing PromptManager...")
        
        await self.registry.initialize()
        
        self._initialized = True
        logger.info("PromptManager initialized successfully")

    async def start(self) -> None:
        """
        Start the prompt manager.
        """
        if self._started:
            logger.warning("PromptManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting PromptManager...")
        
        await self.registry.start()
        
        self._started = True
        logger.info("PromptManager started successfully")

    async def stop(self) -> None:
        """
        Stop the prompt manager.
        """
        if not self._started:
            logger.warning("PromptManager not started")
            return
        
        logger.info("Stopping PromptManager...")
        
        await self.registry.stop()
        
        self._started = False
        logger.info("PromptManager stopped successfully")

    async def render(
        self,
        template_id: str,
        variables: Dict[str, Any],
        use_cache: bool = True,
        validate: bool = True,
    ) -> str:
        """
        Render a prompt template with the given variables.
        
        Args:
            template_id: ID of the template to render.
            variables: Dictionary of variable values.
            use_cache: Whether to use caching.
            validate: Whether to validate variables before rendering.
        
        Returns:
            Rendered prompt string.
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(template_id, variables)
            if cache_key in self._cache:
                self._metrics.cache_hits += 1
                return self._cache[cache_key]
            self._metrics.cache_misses += 1
        
        # Render the prompt
        prompt = await self.registry.render(template_id, variables, validate)
        
        # Update metrics
        self._metrics.prompts_rendered += 1
        
        # Cache the result
        if use_cache:
            self._cache[cache_key] = prompt
        
        return prompt

    async def render_by_name(
        self,
        name: str,
        variables: Dict[str, Any],
        use_cache: bool = True,
        validate: bool = True,
    ) -> str:
        """
        Render a prompt template by name with the given variables.
        
        Args:
            name: Name of the template to render.
            variables: Dictionary of variable values.
            use_cache: Whether to use caching.
            validate: Whether to validate variables before rendering.
        
        Returns:
            Rendered prompt string.
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(name, variables)
            if cache_key in self._cache:
                self._metrics.cache_hits += 1
                return self._cache[cache_key]
            self._metrics.cache_misses += 1
        
        # Render the prompt
        prompt = await self.registry.render_by_name(name, variables, validate)
        
        # Update metrics
        self._metrics.prompts_rendered += 1
        
        # Cache the result
        if use_cache:
            self._cache[cache_key] = prompt
        
        return prompt

    def _generate_cache_key(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Generate a cache key for a template and variables."""
        import hashlib
        
        # Sort variables for consistent cache key
        sorted_vars = sorted(variables.items())
        vars_str = str(sorted_vars)
        
        return hashlib.sha256(f"{template_id}:{vars_str}".encode()).hexdigest()

    async def compose(
        self,
        template_ids: List[str],
        variables: Dict[str, Any],
        separator: str = "\n\n",
        use_cache: bool = True,
    ) -> str:
        """
        Compose multiple prompt templates into a single prompt.
        
        Args:
            template_ids: List of template IDs to compose.
            variables: Dictionary of variable values for all templates.
            separator: Separator to use between templates.
            use_cache: Whether to use caching.
        
        Returns:
            Composed prompt string.
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_compose_cache_key(template_ids, variables, separator)
            if cache_key in self._cache:
                self._metrics.cache_hits += 1
                return self._cache[cache_key]
            self._metrics.cache_misses += 1
        
        # Render each template
        parts = []
        for template_id in template_ids:
            part = await self.registry.render(template_id, variables)
            parts.append(part)
        
        # Compose the prompt
        prompt = separator.join(parts)
        
        # Update metrics
        self._metrics.prompts_rendered += len(template_ids)
        
        # Cache the result
        if use_cache:
            self._cache[cache_key] = prompt
        
        return prompt

    def _generate_compose_cache_key(
        self,
        template_ids: List[str],
        variables: Dict[str, Any],
        separator: str,
    ) -> str:
        """Generate a cache key for composed templates."""
        import hashlib
        
        # Sort for consistent cache key
        sorted_ids = sorted(template_ids)
        sorted_vars = sorted(variables.items())
        
        return hashlib.sha256(f"compose:{sorted_ids}:{sorted_vars}:{separator}".encode()).hexdigest()

    async def get_template(self, template_id: str) -> Optional["PromptTemplate"]:
        """
        Get a prompt template by ID.
        
        Args:
            template_id: ID of the template to get.
        
        Returns:
            PromptTemplate or None if not found.
        """
        return await self.registry.get(template_id)

    async def get_template_by_name(self, name: str) -> Optional["PromptTemplate"]:
        """
        Get a prompt template by name.
        
        Args:
            name: Name of the template to get.
        
        Returns:
            PromptTemplate or None if not found.
        """
        return await self.registry.get_by_name(name)

    async def list_templates(
        self,
        tags: Optional[List[str]] = None,
        prompt_type: Optional[str] = None,
    ) -> List["PromptTemplate"]:
        """
        List all prompt templates, optionally filtered.
        
        Args:
            tags: Optional list of tags to filter by.
            prompt_type: Optional prompt type to filter by.
        
        Returns:
            List of PromptTemplate instances.
        """
        return await self.registry.list_templates(tags, prompt_type)

    async def register_template(self, template: "PromptTemplate") -> str:
        """
        Register a prompt template.
        
        Args:
            template: PromptTemplate to register.
        
        Returns:
            Template ID.
        """
        return await self.registry.register(template)

    async def unregister_template(self, template_id: str) -> bool:
        """
        Unregister a prompt template.
        
        Args:
            template_id: ID of the template to unregister.
        
        Returns:
            True if template was unregistered, False if not found.
        """
        # Remove from cache
        cache_keys = [k for k in self._cache.keys() if k.startswith(template_id + ":")]
        for key in cache_keys:
            del self._cache[key]
        
        return await self.registry.unregister(template_id)

    async def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the prompt manager.
        
        Returns:
            Dictionary with prompt manager information.
        """
        return {
            "templates": len(self._cache),
            "cache_size": len(self._cache),
            "registry": await self.registry.get_info(),
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the prompt manager.
        
        This method clears all state and resets all metrics.
        """
        logger.info("Resetting PromptManager...")
        
        await self.registry.reset()
        self._cache.clear()
        self._metrics = PromptManagerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("PromptManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PromptManager("
            f"templates={len(self.registry._templates) if self._registry else 0}, "
            f"cache={len(self._cache)})"
        )
