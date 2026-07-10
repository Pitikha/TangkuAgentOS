"""
AI Foundation Framework - Context Assembler

This module provides the ContextAssembler class for automatically building
AI context from various sources.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.context.context import AIContext, ContextSource
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class ContextAssemblerMetrics:
    """Metrics for the context assembler."""
    contexts_assembled: int = 0
    sources_used: Dict[str, int] = field(default_factory=dict)
    tokens_assembled: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contexts_assembled": self.contexts_assembled,
            "sources_used": self.sources_used.copy(),
            "tokens_assembled": self.tokens_assembled,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ContextAssembler:
    """
    Assembles AI context from various sources.
    
    This class automatically collects and combines context information from
    multiple sources including conversation history, memory, knowledge,
    workspace state, repository information, and more.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ContextAssembler
        >>> 
        >>> # Create assembler
        >>> assembler = ContextAssembler()
        >>> 
        >>> # Assemble context for a request
        >>> context = await assembler.assemble(
        ...     session_id="session123",
        ...     conversation_id="conv123",
        ...     request={"prompt": "Hello"}
        ... )
        >>> 
        >>> # Use context in AI request
        >>> response = await ai_foundation.execute(
        ...     prompt="Hello",
        ...     context=context.to_dict()
        ... )
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the context assembler.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = ContextAssemblerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ContextAssembler initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> ContextAssemblerMetrics:
        """Get the context assembler metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the assembler is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the assembler is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the context assembler.
        """
        if self._initialized:
            logger.warning("ContextAssembler already initialized")
            return
        
        logger.info("Initializing ContextAssembler...")
        
        self._initialized = True
        logger.info("ContextAssembler initialized successfully")

    async def start(self) -> None:
        """
        Start the context assembler.
        """
        if self._started:
            logger.warning("ContextAssembler already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ContextAssembler...")
        
        self._started = True
        logger.info("ContextAssembler started successfully")

    async def stop(self) -> None:
        """
        Stop the context assembler.
        """
        if not self._started:
            logger.warning("ContextAssembler not started")
            return
        
        logger.info("Stopping ContextAssembler...")
        
        self._started = False
        logger.info("ContextAssembler stopped successfully")

    async def assemble(
        self,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        request: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        include_sources: Optional[Set[str]] = None,
        exclude_sources: Optional[Set[str]] = None,
    ) -> "AIContext":
        """
        Assemble context from various sources.
        
        Args:
            session_id: ID of the session.
            conversation_id: ID of the conversation.
            request: The AI request being processed.
            context: Additional context to include.
            include_sources: Set of sources to include (None = all).
            exclude_sources: Set of sources to exclude.
        
        Returns:
            AIContext with assembled context.
        """
        from tangku_agentos.ai_foundation.context.context import AIContext, ContextSource
        
        async with self._lock:
            self._metrics.contexts_assembled += 1
            
            # Create context
            ai_context = AIContext()
            
            # Determine which sources to use
            sources_to_use = self._get_sources_to_use(include_sources, exclude_sources)
            
            # Assemble context from each source
            for source in sources_to_use:
                try:
                    await self._assemble_from_source(
                        ai_context, source, session_id, conversation_id, request, context
                    )
                    self._metrics.sources_used[source.value] = \
                        self._metrics.sources_used.get(source.value, 0) + 1
                except Exception as e:
                    self._metrics.errors += 1
                    self._metrics.last_error = str(e)
                    self._metrics.last_error_time = datetime.utcnow()
                    logger.error(f"Error assembling context from {source.value}: {e}")
            
            # Update token count
            self._metrics.tokens_assembled = ai_context.tokens if hasattr(ai_context, 'tokens') else 0
            
            return ai_context

    def _get_sources_to_use(
        self,
        include_sources: Optional[Set[str]],
        exclude_sources: Optional[Set[str]]
    ) -> Set[ContextSource]:
        """Determine which sources to use for context assembly."""
        from tangku_agentos.ai_foundation.context.context import ContextSource
        
        # Get configured sources
        configured_sources = set()
        if self._config.context.include_conversation:
            configured_sources.add(ContextSource.CONVERSATION)
        if self._config.context.include_memory:
            configured_sources.add(ContextSource.MEMORY)
        if self._config.context.include_knowledge:
            configured_sources.add(ContextSource.KNOWLEDGE)
        if self._config.context.include_workspace:
            configured_sources.add(ContextSource.WORKSPACE)
        if self._config.context.include_repository:
            configured_sources.add(ContextSource.REPOSITORY)
        if self._config.context.include_terminal:
            configured_sources.add(ContextSource.TERMINAL)
        if self._config.context.include_system:
            configured_sources.add(ContextSource.SYSTEM)
        if self._config.context.include_runtime:
            configured_sources.add(ContextSource.RUNTIME)
        if self._config.context.include_user:
            configured_sources.add(ContextSource.USER)
        
        # Apply include filter
        if include_sources:
            configured_sources = {
                s for s in configured_sources
                if s.value in include_sources or s.name in include_sources
            }
        
        # Apply exclude filter
        if exclude_sources:
            configured_sources = {
                s for s in configured_sources
                if s.value not in exclude_sources and s.name not in exclude_sources
            }
        
        return configured_sources

    async def _assemble_from_source(
        self,
        context: "AIContext",
        source: "ContextSource",
        session_id: Optional[str],
        conversation_id: Optional[str],
        request: Optional[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from a specific source."""
        if source == ContextSource.CONVERSATION:
            await self._assemble_conversation_context(context, session_id, conversation_id, request)
        elif source == ContextSource.MEMORY:
            await self._assemble_memory_context(context, session_id, request)
        elif source == ContextSource.KNOWLEDGE:
            await self._assemble_knowledge_context(context, session_id, request)
        elif source == ContextSource.WORKSPACE:
            await self._assemble_workspace_context(context, session_id, request)
        elif source == ContextSource.REPOSITORY:
            await self._assemble_repository_context(context, session_id, request)
        elif source == ContextSource.TERMINAL:
            await self._assemble_terminal_context(context, session_id, request)
        elif source == ContextSource.SYSTEM:
            await self._assemble_system_context(context, session_id, request)
        elif source == ContextSource.RUNTIME:
            await self._assemble_runtime_context(context, session_id, request)
        elif source == ContextSource.USER:
            await self._assemble_user_context(context, session_id, request)
        elif source == ContextSource.CUSTOM:
            await self._assemble_custom_context(context, additional_context)

    async def _assemble_conversation_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        conversation_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from conversation history."""
        if not conversation_id:
            return
        
        try:
            # Get conversation messages
            messages = await self._foundation.conversations.get_messages(conversation_id)
            
            if not messages:
                return
            
            # Add conversation history to context
            max_messages = self._config.context.max_context_messages
            recent_messages = messages[-max_messages:] if max_messages else messages
            
            for i, message in enumerate(recent_messages):
                context.add(
                    key=f"conversation_message_{i}",
                    value=message.to_dict() if hasattr(message, 'to_dict') else str(message),
                    source=ContextSource.CONVERSATION,
                    priority=len(recent_messages) - i  # More recent = higher priority
                )
            
            # Add conversation summary
            if len(messages) > max_messages:
                context.add(
                    key="conversation_summary",
                    value=f"Conversation has {len(messages)} messages, showing last {max_messages}",
                    source=ContextSource.CONVERSATION,
                    priority=0
                )
        
        except Exception as e:
            logger.warning(f"Error assembling conversation context: {e}")

    async def _assemble_memory_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from memory."""
        if not self._config.memory.enabled:
            return
        
        try:
            # Get relevant memory entries
            query = request.get("prompt", "") if request else ""
            memories = await self._foundation.memory.retrieve(
                query=query,
                limit=self._config.context.max_context_length // 100  # Rough estimate
            )
            
            if not memories:
                return
            
            # Add memory entries to context
            for i, memory in enumerate(memories):
                context.add(
                    key=f"memory_{i}",
                    value=memory,
                    source=ContextSource.MEMORY,
                    priority=len(memories) - i  # More recent = higher priority
                )
        
        except Exception as e:
            logger.warning(f"Error assembling memory context: {e}")

    async def _assemble_knowledge_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from knowledge."""
        if not self._config.knowledge.enabled:
            return
        
        try:
            # Get relevant knowledge entries
            query = request.get("prompt", "") if request else ""
            knowledge = await self._foundation.knowledge.retrieve(
                query=query,
                limit=self._config.context.max_context_length // 100  # Rough estimate
            )
            
            if not knowledge:
                return
            
            # Add knowledge entries to context
            for i, entry in enumerate(knowledge.get("results", [])):
                context.add(
                    key=f"knowledge_{i}",
                    value=entry,
                    source=ContextSource.KNOWLEDGE,
                    priority=len(knowledge.get("results", [])) - i
                )
        
        except Exception as e:
            logger.warning(f"Error assembling knowledge context: {e}")

    async def _assemble_workspace_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from workspace."""
        try:
            # In a real implementation, this would integrate with the Workspace Engine
            # For now, add placeholder workspace context
            context.add(
                key="workspace",
                value={"status": "active", "files": []},
                source=ContextSource.WORKSPACE,
                priority=0
            )
        
        except Exception as e:
            logger.warning(f"Error assembling workspace context: {e}")

    async def _assemble_repository_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from repository."""
        try:
            # In a real implementation, this would integrate with the Repository Intelligence
            # For now, add placeholder repository context
            context.add(
                key="repository",
                value={"status": "active", "branches": []},
                source=ContextSource.REPOSITORY,
                priority=0
            )
        
        except Exception as e:
            logger.warning(f"Error assembling repository context: {e}")

    async def _assemble_terminal_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from terminal."""
        try:
            # In a real implementation, this would integrate with the Terminal Runtime
            # For now, add placeholder terminal context
            context.add(
                key="terminal",
                value={"status": "active", "output": ""},
                source=ContextSource.TERMINAL,
                priority=0
            )
        
        except Exception as e:
            logger.warning(f"Error assembling terminal context: {e}")

    async def _assemble_system_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from system state."""
        try:
            # Add system information
            context.add(
                key="system",
                value={
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "TangkuAgentOS",
                    "version": "1.0.0"
                },
                source=ContextSource.SYSTEM,
                priority=0
            )
        
        except Exception as e:
            logger.warning(f"Error assembling system context: {e}")

    async def _assemble_runtime_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from runtime state."""
        try:
            # In a real implementation, this would integrate with the Runtime Communication Framework
            # For now, add placeholder runtime context
            context.add(
                key="runtime",
                value={"status": "active", "agents": []},
                source=ContextSource.RUNTIME,
                priority=0
            )
        
        except Exception as e:
            logger.warning(f"Error assembling runtime context: {e}")

    async def _assemble_user_context(
        self,
        context: "AIContext",
        session_id: Optional[str],
        request: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from user information."""
        try:
            # Get session for user information
            if session_id:
                session = await self._foundation.sessions.get(session_id)
                if session and session.user_id:
                    context.add(
                        key="user_id",
                        value=session.user_id,
                        source=ContextSource.USER,
                        priority=10  # High priority
                    )
            
            # Add user preferences if available
            if request and "user_preferences" in request:
                context.add(
                    key="user_preferences",
                    value=request["user_preferences"],
                    source=ContextSource.USER,
                    priority=5
                )
        
        except Exception as e:
            logger.warning(f"Error assembling user context: {e}")

    async def _assemble_custom_context(
        self,
        context: "AIContext",
        additional_context: Optional[Dict[str, Any]],
    ) -> None:
        """Assemble context from custom sources."""
        if not additional_context:
            return
        
        for key, value in additional_context.items():
            context.add(
                key=key,
                value=value,
                source=ContextSource.CUSTOM,
                priority=0
            )

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the context assembler.
        
        Returns:
            Dictionary with context assembler information.
        """
        return {
            "metrics": self._metrics.to_dict(),
            "config": {
                "include_conversation": self._config.context.include_conversation,
                "include_memory": self._config.context.include_memory,
                "include_knowledge": self._config.context.include_knowledge,
                "include_workspace": self._config.context.include_workspace,
                "include_repository": self._config.context.include_repository,
                "include_terminal": self._config.context.include_terminal,
                "include_system": self._config.context.include_system,
                "include_runtime": self._config.context.include_runtime,
                "include_user": self._config.context.include_user,
            }
        }

    async def reset(self) -> None:
        """
        Reset the context assembler.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting ContextAssembler...")
        
        self._metrics = ContextAssemblerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("ContextAssembler reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ContextAssembler("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"contexts={self._metrics.contexts_assembled})"
        )
