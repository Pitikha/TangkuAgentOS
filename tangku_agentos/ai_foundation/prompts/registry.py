"""
AI Foundation Framework - Prompt Registry

This module provides the PromptRegistry class for managing prompt templates.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.prompts.template import PromptTemplate
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class PromptRegistryMetrics:
    """Metrics for the prompt registry."""
    templates_registered: int = 0
    templates_used: int = 0
    renderings: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "templates_registered": self.templates_registered,
            "templates_used": self.templates_used,
            "renderings": self.renderings,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class PromptRegistry:
    """
    Registry for managing prompt templates.
    
    This class provides a centralized way to register, manage, and use
    prompt templates. It supports template versioning, tagging, and
    categorization.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import PromptRegistry
        >>> 
        >>> # Create registry
        >>> registry = PromptRegistry()
        >>> 
        >>> # Register a template
        >>> template = PromptTemplate(
        ...     name="greeting",
        ...     content="Hello, {name}! How can I help you today?",
        ...     variables=[PromptVariable(name="name", required=True)]
        ... )
        >>> await registry.register(template)
        >>> 
        >>> # Render a template
        >>> rendered = await registry.render("greeting", {"name": "Alice"})
        >>> print(rendered)
        Hello, Alice! How can I help you today?
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the prompt registry.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._templates: Dict[str, "PromptTemplate"] = {}
        self._name_index: Dict[str, str] = {}  # name -> template_id
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of template_ids
        self._metrics = PromptRegistryMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("PromptRegistry initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> PromptRegistryMetrics:
        """Get the prompt registry metrics."""
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
        Initialize the prompt registry.
        """
        if self._initialized:
            logger.warning("PromptRegistry already initialized")
            return
        
        logger.info("Initializing PromptRegistry...")
        
        # Load default templates
        await self._load_default_templates()
        
        self._initialized = True
        logger.info("PromptRegistry initialized successfully")

    async def start(self) -> None:
        """
        Start the prompt registry.
        """
        if self._started:
            logger.warning("PromptRegistry already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting PromptRegistry...")
        
        self._started = True
        logger.info("PromptRegistry started successfully")

    async def stop(self) -> None:
        """
        Stop the prompt registry.
        """
        if not self._started:
            logger.warning("PromptRegistry not started")
            return
        
        logger.info("Stopping PromptRegistry...")
        
        self._started = False
        logger.info("PromptRegistry stopped successfully")

    async def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        from tangku_agentos.ai_foundation.prompts.template import PromptTemplate, PromptVariable
        
        # Default system prompt
        system_template = PromptTemplate(
            name="default_system",
            content="You are a helpful AI assistant. Be accurate, concise, and helpful.",
            prompt_type="SYSTEM",
            description="Default system prompt for AI assistants",
            tags=["system", "default"],
        )
        await self.register(system_template)
        
        # Default user prompt
        user_template = PromptTemplate(
            name="default_user",
            content="{prompt}",
            prompt_type="USER",
            variables=[PromptVariable(name="prompt", required=True)],
            description="Default user prompt template",
            tags=["user", "default"],
        )
        await self.register(user_template)
        
        # Chat template
        chat_template = PromptTemplate(
            name="chat",
            content="{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
            prompt_type="CHAT",
            variables=[
                PromptVariable(name="system_prompt", default="You are a helpful AI assistant."),
                PromptVariable(name="user_prompt", required=True),
            ],
            description="Basic chat template with system and user prompts",
            tags=["chat", "default"],
        )
        await self.register(chat_template)
        
        # Completion template
        completion_template = PromptTemplate(
            name="completion",
            content="{prompt}",
            prompt_type="COMPLETION",
            variables=[PromptVariable(name="prompt", required=True)],
            description="Basic completion template",
            tags=["completion", "default"],
        )
        await self.register(completion_template)

    async def register(self, template: "PromptTemplate") -> str:
        """
        Register a prompt template.
        
        Args:
            template: PromptTemplate to register.
        
        Returns:
            Template ID.
        
        Raises:
            ValueError: If template with same ID or name already exists.
        """
        async with self._lock:
            # Check if template with same ID already exists
            if template.template_id in self._templates:
                raise ValueError(f"Template with ID {template.template_id} already exists")
            
            # Check if template with same name already exists
            if template.name in self._name_index:
                raise ValueError(f"Template with name {template.name} already exists")
            
            # Register template
            self._templates[template.template_id] = template
            self._name_index[template.name] = template.template_id
            
            # Index by tags
            for tag in template.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(template.template_id)
            
            self._metrics.templates_registered += 1
            
            logger.debug(f"Prompt template registered: {template.template_id}")
            return template.template_id

    async def unregister(self, template_id: str) -> bool:
        """
        Unregister a prompt template.
        
        Args:
            template_id: ID of the template to unregister.
        
        Returns:
            True if template was unregistered, False if not found.
        """
        async with self._lock:
            if template_id not in self._templates:
                return False
            
            template = self._templates[template_id]
            
            # Remove from name index
            if template.name in self._name_index:
                del self._name_index[template.name]
            
            # Remove from tag index
            for tag in template.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(template_id)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]
            
            # Remove from templates
            del self._templates[template_id]
            
            self._metrics.templates_registered -= 1
            
            logger.debug(f"Prompt template unregistered: {template_id}")
            return True

    async def get(self, template_id: str) -> Optional["PromptTemplate"]:
        """
        Get a prompt template by ID.
        
        Args:
            template_id: ID of the template to get.
        
        Returns:
            PromptTemplate or None if not found.
        """
        return self._templates.get(template_id)

    async def get_by_name(self, name: str) -> Optional["PromptTemplate"]:
        """
        Get a prompt template by name.
        
        Args:
            name: Name of the template to get.
        
        Returns:
            PromptTemplate or None if not found.
        """
        template_id = self._name_index.get(name)
        if template_id:
            return self._templates.get(template_id)
        return None

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
        templates = []
        
        for template in self._templates.values():
            # Filter by tags
            if tags:
                if not any(tag in template.tags for tag in tags):
                    continue
            
            # Filter by prompt type
            if prompt_type:
                if template.prompt_type.value != prompt_type:
                    continue
            
            templates.append(template)
        
        return templates

    async def get_by_tags(self, tags: List[str]) -> List["PromptTemplate"]:
        """
        Get prompt templates by tags.
        
        Args:
            tags: List of tags to filter by.
        
        Returns:
            List of PromptTemplate instances.
        """
        template_ids = set()
        
        for tag in tags:
            if tag in self._tag_index:
                if not template_ids:
                    template_ids.update(self._tag_index[tag])
                else:
                    template_ids.intersection_update(self._tag_index[tag])
        
        return [self._templates[tid] for tid in template_ids if tid in self._templates]

    async def render(self, template_id: str, variables: Dict[str, Any], validate: bool = True) -> str:
        """
        Render a prompt template with the given variables.
        
        Args:
            template_id: ID of the template to render.
            variables: Dictionary of variable values.
            validate: Whether to validate variables before rendering.
        
        Returns:
            Rendered prompt string.
        
        Raises:
            ValueError: If template not found or validation fails.
        """
        template = await self.get(template_id)
        if not template:
            raise ValueError(f"Prompt template not found: {template_id}")
        
        self._metrics.templates_used += 1
        self._metrics.renderings += 1
        
        return template.render(variables, validate)

    async def render_by_name(self, name: str, variables: Dict[str, Any], validate: bool = True) -> str:
        """
        Render a prompt template by name with the given variables.
        
        Args:
            name: Name of the template to render.
            variables: Dictionary of variable values.
            validate: Whether to validate variables before rendering.
        
        Returns:
            Rendered prompt string.
        
        Raises:
            ValueError: If template not found or validation fails.
        """
        template = await self.get_by_name(name)
        if not template:
            raise ValueError(f"Prompt template not found: {name}")
        
        self._metrics.templates_used += 1
        self._metrics.renderings += 1
        
        return template.render(variables, validate)

    async def update(self, template_id: str, **kwargs) -> bool:
        """
        Update a prompt template.
        
        Args:
            template_id: ID of the template to update.
            **kwargs: Template attributes to update.
        
        Returns:
            True if template was updated, False if not found.
        """
        async with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return False
            
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.utcnow()
            return True

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the prompt registry.
        
        Returns:
            Dictionary with prompt registry information.
        """
        return {
            "templates": len(self._templates),
            "tags": list(self._tag_index.keys()),
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the prompt registry.
        
        This method clears all templates and resets all state.
        """
        logger.info("Resetting PromptRegistry...")
        
        async with self._lock:
            self._templates.clear()
            self._name_index.clear()
            self._tag_index.clear()
            self._metrics = PromptRegistryMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("PromptRegistry reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PromptRegistry("
            f"templates={len(self._templates)}, "
            f"tags={len(self._tag_index)})"
        )
