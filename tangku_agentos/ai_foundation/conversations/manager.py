"""
AI Foundation Framework - Conversation Manager

This module provides the ConversationManager class for managing AI conversations.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.conversations.conversation import Conversation
    from tangku_agentos.ai_foundation.models.message import Message, MessageRole
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class ConversationManagerMetrics:
    """Metrics for the conversation manager."""
    conversations_created: int = 0
    conversations_activated: int = 0
    conversations_completed: int = 0
    conversations_archived: int = 0
    conversations_expired: int = 0
    messages_added: int = 0
    messages_removed: int = 0
    active_conversations: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conversations_created": self.conversations_created,
            "conversations_activated": self.conversations_activated,
            "conversations_completed": self.conversations_completed,
            "conversations_archived": self.conversations_archived,
            "conversations_expired": self.conversations_expired,
            "messages_added": self.messages_added,
            "messages_removed": self.messages_removed,
            "active_conversations": self.active_conversations,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ConversationManager:
    """
    Manager for AI conversations.
    
    This class provides methods for creating, managing, and tracking AI conversations.
    It handles conversation lifecycle, expiration, and cleanup.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ConversationManager
        >>> 
        >>> # Create manager
        >>> manager = ConversationManager()
        >>> 
        >>> # Create a conversation
        >>> conversation = await manager.create(session_id="session123", user_id="user123")
        >>> 
        >>> # Add a message
        >>> await manager.add_message(conversation.conversation_id, role="user", content="Hello")
        >>> 
        >>> # Get conversation
        >>> conversation = manager.get(conversation.conversation_id)
        >>> 
        >>> # List conversations
        >>> conversations = manager.list_conversations()
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the conversation manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._conversations: Dict[str, "Conversation"] = {}
        self._session_conversations: Dict[str, Set[str]] = {}  # session_id -> set of conversation_ids
        self._user_conversations: Dict[str, Set[str]] = {}  # user_id -> set of conversation_ids
        self._metrics = ConversationManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("ConversationManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> ConversationManagerMetrics:
        """Get the conversation manager metrics."""
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
        Initialize the conversation manager.
        """
        if self._initialized:
            logger.warning("ConversationManager already initialized")
            return
        
        logger.info("Initializing ConversationManager...")
        
        self._initialized = True
        logger.info("ConversationManager initialized successfully")

    async def start(self) -> None:
        """
        Start the conversation manager.
        
        This method starts the cleanup task for expired conversations.
        """
        if self._started:
            logger.warning("ConversationManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ConversationManager...")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_conversations())
        
        self._started = True
        logger.info("ConversationManager started successfully")

    async def stop(self) -> None:
        """
        Stop the conversation manager.
        
        This method stops the cleanup task and cleans up resources.
        """
        if not self._started:
            logger.warning("ConversationManager not started")
            return
        
        logger.info("Stopping ConversationManager...")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._started = False
        logger.info("ConversationManager stopped successfully")

    async def _cleanup_expired_conversations(self) -> None:
        """Clean up expired conversations periodically."""
        import time
        
        cleanup_interval = self._config.sessions.conversation_cleanup_interval
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during conversation cleanup: {e}")

    async def _cleanup_expired(self) -> None:
        """Clean up expired conversations."""
        async with self._lock:
            expired_conversations = []
            
            for conv_id, conversation in self._conversations.items():
                if conversation.is_expired:
                    expired_conversations.append(conv_id)
            
            for conv_id in expired_conversations:
                await self._remove_conversation(conv_id, expired=True)

    async def create(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Conversation":
        """
        Create a new conversation.
        
        Args:
            session_id: ID of the session this conversation belongs to.
            user_id: ID of the user participating in the conversation.
            model: Model to use for the conversation.
            provider: Provider to use for the conversation.
            metadata: Additional metadata.
        
        Returns:
            Conversation instance.
        """
        from tangku_agentos.ai_foundation.conversations.conversation import Conversation
        
        async with self._lock:
            # Check conversation limit per session
            max_conversations = self._config.sessions.max_conversations_per_session
            if session_id and session_id in self._session_conversations:
                if len(self._session_conversations[session_id]) >= max_conversations:
                    # Remove oldest conversation for this session
                    await self._remove_oldest_conversation(session_id)
            
            # Create conversation
            conversation = Conversation(
                session_id=session_id,
                user_id=user_id,
                model=model or self._config.models.default_chat_model,
                provider=provider or self._config.providers.default_provider,
                metadata=metadata or {},
            )
            
            # Store conversation
            self._conversations[conversation.conversation_id] = conversation
            
            # Index by session
            if session_id:
                if session_id not in self._session_conversations:
                    self._session_conversations[session_id] = set()
                self._session_conversations[session_id].add(conversation.conversation_id)
            
            # Index by user
            if user_id:
                if user_id not in self._user_conversations:
                    self._user_conversations[user_id] = set()
                self._user_conversations[user_id].add(conversation.conversation_id)
            
            # Update metrics
            self._metrics.conversations_created += 1
            self._metrics.active_conversations = len(self._conversations)
            
            logger.debug(f"Conversation created: {conversation.conversation_id}")
            return conversation

    async def get(self, conversation_id: str) -> Optional["Conversation"]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to get.
        
        Returns:
            Conversation instance or None if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation and conversation.is_expired:
                await self._remove_conversation(conversation_id, expired=True)
                return None
            return conversation

    async def get_by_session(self, session_id: str) -> List["Conversation"]:
        """
        Get all conversations for a specific session.
        
        Args:
            session_id: ID of the session.
        
        Returns:
            List of Conversation instances.
        """
        async with self._lock:
            conv_ids = self._session_conversations.get(session_id, set())
            conversations = []
            
            for conv_id in conv_ids:
                conversation = self._conversations.get(conv_id)
                if conversation and not conversation.is_expired:
                    conversations.append(conversation)
            
            return conversations

    async def get_by_user(self, user_id: str) -> List["Conversation"]:
        """
        Get all conversations for a specific user.
        
        Args:
            user_id: ID of the user.
        
        Returns:
            List of Conversation instances.
        """
        async with self._lock:
            conv_ids = self._user_conversations.get(user_id, set())
            conversations = []
            
            for conv_id in conv_ids:
                conversation = self._conversations.get(conv_id)
                if conversation and not conversation.is_expired:
                    conversations.append(conversation)
            
            return conversations

    async def list_conversations(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List["Conversation"]:
        """
        List all conversations, optionally filtered.
        
        Args:
            session_id: Optional session ID to filter by.
            user_id: Optional user ID to filter by.
            status: Optional status to filter by.
        
        Returns:
            List of Conversation instances.
        """
        async with self._lock:
            conversations = []
            
            for conversation in self._conversations.values():
                if conversation.is_expired:
                    continue
                
                if session_id and conversation.session_id != session_id:
                    continue
                if user_id and conversation.user_id != user_id:
                    continue
                if status and conversation.status.value != status:
                    continue
                
                conversations.append(conversation)
            
            return conversations

    async def add_message(
        self,
        conversation_id: str,
        message: "Message",
    ) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation.
            message: Message to add.
        
        Returns:
            True if message was added, False if conversation not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return False
            
            conversation.add_message(message)
            self._metrics.messages_added += 1
            
            logger.debug(f"Message added to conversation: {conversation_id}")
            return True

    async def add_message_dict(
        self,
        conversation_id: str,
        role: str,
        content: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a message to a conversation using dictionary parameters.
        
        Args:
            conversation_id: ID of the conversation.
            role: Role of the message.
            content: Content of the message.
            name: Optional name for the sender.
            tool_call_id: Optional tool call ID.
            tool_calls: Optional tool calls.
            metadata: Optional metadata.
        
        Returns:
            True if message was added, False if conversation not found.
        """
        from tangku_agentos.ai_foundation.models.message import Message, MessageRole
        
        try:
            message_role = MessageRole(role)
        except ValueError:
            message_role = MessageRole.USER
        
        message = Message(
            role=message_role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            tool_calls=tool_calls or [],
            metadata=metadata or {},
        )
        
        return await self.add_message(conversation_id, message)

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> List["Message"]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: ID of the conversation.
            limit: Optional limit on number of messages.
        
        Returns:
            List of Message instances.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return []
            
            return conversation.get_messages(limit)

    async def get_last_message(self, conversation_id: str) -> Optional["Message"]:
        """
        Get the last message from a conversation.
        
        Args:
            conversation_id: ID of the conversation.
        
        Returns:
            Message instance or None if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return None
            
            return conversation.get_last_message()

    async def remove_last_message(self, conversation_id: str) -> Optional["Message"]:
        """
        Remove the last message from a conversation.
        
        Args:
            conversation_id: ID of the conversation.
        
        Returns:
            Removed Message instance or None if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return None
            
            message = conversation.remove_last_message()
            if message:
                self._metrics.messages_removed += 1
            return message

    async def clear_messages(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation.
        
        Args:
            conversation_id: ID of the conversation.
        
        Returns:
            True if messages were cleared, False if conversation not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return False
            
            conversation.clear_messages()
            return True

    async def activate(self, conversation_id: str) -> Optional["Conversation"]:
        """
        Activate a conversation.
        
        Args:
            conversation_id: ID of the conversation to activate.
        
        Returns:
            Conversation instance or None if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.activate()
                self._metrics.conversations_activated += 1
                logger.debug(f"Conversation activated: {conversation_id}")
            return conversation

    async def complete(self, conversation_id: str) -> bool:
        """
        Mark a conversation as completed.
        
        Args:
            conversation_id: ID of the conversation to complete.
        
        Returns:
            True if conversation was completed, False if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.complete()
                self._metrics.conversations_completed += 1
                logger.debug(f"Conversation completed: {conversation_id}")
                return True
            return False

    async def archive(self, conversation_id: str) -> bool:
        """
        Archive a conversation.
        
        Args:
            conversation_id: ID of the conversation to archive.
        
        Returns:
            True if conversation was archived, False if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.archive()
                self._metrics.conversations_archived += 1
                logger.debug(f"Conversation archived: {conversation_id}")
                return True
            return False

    async def close(self, conversation_id: str) -> bool:
        """
        Close a conversation (complete and archive).
        
        Args:
            conversation_id: ID of the conversation to close.
        
        Returns:
            True if conversation was closed, False if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if conversation:
                conversation.complete()
                conversation.archive()
                self._metrics.conversations_completed += 1
                self._metrics.conversations_archived += 1
                logger.debug(f"Conversation closed: {conversation_id}")
                return True
            return False

    async def close_all(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> int:
        """
        Close all conversations, optionally filtered.
        
        Args:
            session_id: Optional session ID to filter by.
            user_id: Optional user ID to filter by.
        
        Returns:
            Number of conversations closed.
        """
        async with self._lock:
            if session_id:
                conv_ids = list(self._session_conversations.get(session_id, set()))
            elif user_id:
                conv_ids = list(self._user_conversations.get(user_id, set()))
            else:
                conv_ids = list(self._conversations.keys())
            
            count = 0
            for conv_id in conv_ids:
                if await self.close(conv_id):
                    count += 1
            
            return count

    async def _remove_conversation(self, conversation_id: str, expired: bool = False) -> bool:
        """
        Remove a conversation from the manager.
        
        Args:
            conversation_id: ID of the conversation to remove.
            expired: Whether the conversation expired.
        
        Returns:
            True if conversation was removed, False if not found.
        """
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return False
        
        # Remove from session index
        if conversation.session_id and conversation.session_id in self._session_conversations:
            self._session_conversations[conversation.session_id].discard(conversation_id)
            if not self._session_conversations[conversation.session_id]:
                del self._session_conversations[conversation.session_id]
        
        # Remove from user index
        if conversation.user_id and conversation.user_id in self._user_conversations:
            self._user_conversations[conversation.user_id].discard(conversation_id)
            if not self._user_conversations[conversation.user_id]:
                del self._user_conversations[conversation.user_id]
        
        # Remove from conversations
        del self._conversations[conversation_id]
        
        # Update metrics
        if expired:
            self._metrics.conversations_expired += 1
        self._metrics.active_conversations = len(self._conversations)
        
        logger.debug(f"Conversation removed: {conversation_id} (expired={expired})")
        return True

    async def _remove_oldest_conversation(self, session_id: str) -> bool:
        """
        Remove the oldest conversation for a session.
        
        Args:
            session_id: ID of the session.
        
        Returns:
            True if a conversation was removed, False otherwise.
        """
        conv_ids = self._session_conversations.get(session_id, set())
        if not conv_ids:
            return False
        
        # Find oldest conversation
        oldest_id = min(
            [cid for cid in conv_ids if cid in self._conversations],
            key=lambda cid: self._conversations[cid].created_at
        )
        return await self._remove_conversation(oldest_id)

    async def update(self, conversation_id: str, **kwargs) -> bool:
        """
        Update a conversation.
        
        Args:
            conversation_id: ID of the conversation to update.
            **kwargs: Conversation attributes to update.
        
        Returns:
            True if conversation was updated, False if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return False
            
            for key, value in kwargs.items():
                if hasattr(conversation, key):
                    setattr(conversation, key, value)
            
            conversation.updated_at = datetime.utcnow()
            return True

    async def extend(self, conversation_id: str, hours: float = 24.0) -> bool:
        """
        Extend a conversation's expiration.
        
        Args:
            conversation_id: ID of the conversation to extend.
            hours: Number of hours to extend.
        
        Returns:
            True if conversation was extended, False if not found.
        """
        async with self._lock:
            conversation = self._conversations.get(conversation_id)
            if not conversation:
                return False
            
            conversation.extend(hours)
            return True

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the conversation manager.
        
        Returns:
            Dictionary with conversation manager information.
        """
        return {
            "conversations": len(self._conversations),
            "active_conversations": self._metrics.active_conversations,
            "session_conversations": {session: len(convs) for session, convs in self._session_conversations.items()},
            "user_conversations": {user: len(convs) for user, convs in self._user_conversations.items()},
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the conversation manager.
        
        This method clears all conversations and resets all state.
        """
        logger.info("Resetting ConversationManager...")
        
        async with self._lock:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clear all conversations
            self._conversations.clear()
            self._session_conversations.clear()
            self._user_conversations.clear()
            
            # Reset metrics
            self._metrics = ConversationManagerMetrics()
            
            # Reset state
            self._initialized = False
            self._started = False
            self._cleanup_task = None
        
        logger.info("ConversationManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ConversationManager("
            f"conversations={len(self._conversations)}, "
            f"active={self._metrics.active_conversations})"
        )
