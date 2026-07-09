"""
Context Assembler for TangkuAgentOS AI Foundation Framework.

This module collects and assembles context from various sources for AI requests.
"""

from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from ..sessions.session_manager import AISession
from ..conversations.conversation_manager import Conversation
from ..memory.memory_connector import MemoryConnector
from ..knowledge.knowledge_connector import KnowledgeConnector


@dataclass
class ContextSource:
    """Represents a source of context for AI requests."""
    name: str
    data: Any
    priority: int = 0


class ContextAssembler:
    """Assembles context from multiple sources for AI requests."""

    def __init__(
        self,
        memory_connector: Optional[MemoryConnector] = None,
        knowledge_connector: Optional[KnowledgeConnector] = None,
    ):
        self._memory_connector = memory_connector
        self._knowledge_connector = knowledge_connector

    async def assemble_context(
        self,
        session: AISession,
        conversation: Optional[Conversation] = None,
        additional_sources: Optional[List[ContextSource]] = None,
    ) -> Dict[str, Any]:
        """Assemble context from all available sources."""
        context: Dict[str, Any] = {
            "session": {
                "session_id": str(session.session_id),
                "model": session.model.name,
                "provider": session.provider.name,
            },
            "conversation": {
                "messages": [msg for msg in (conversation.messages if conversation else [])],
            },
            "memory": {},
            "knowledge": {},
        }

        # Add memory context
        if self._memory_connector:
            memory_context = await self._memory_connector.retrieve(
                session.memory_references
            )
            context["memory"] = memory_context

        # Add knowledge context
        if self._knowledge_connector:
            knowledge_context = await self._knowledge_connector.retrieve(
                session.knowledge_references
            )
            context["knowledge"] = knowledge_context

        # Add additional sources
        if additional_sources:
            for source in additional_sources:
                context[source.name] = source.data

        return context

    async def optimize_context(
        self,
        context: Dict[str, Any],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Optimize context to fit within a token budget."""
        # Simple optimization: Truncate strings and lists
        optimized = {}
        for key, value in context.items():
            if isinstance(value, str) and len(value) > max_tokens:
                optimized[key] = value[:max_tokens]
            elif isinstance(value, list) and len(value) > max_tokens:
                optimized[key] = value[:max_tokens]
            else:
                optimized[key] = value
        return optimized
