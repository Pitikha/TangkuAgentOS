"""
AI Foundation Framework - Core Foundation Class

The AIFoundation class is the main entry point for the AI Foundation Framework.
It provides a unified interface for all AI operations while maintaining complete
provider independence.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.providers.registry import ProviderRegistry
    from tangku_agentos.ai_foundation.sessions.manager import SessionManager
    from tangku_agentos.ai_foundation.conversations.manager import ConversationManager
    from tangku_agentos.ai_foundation.context.assembler import ContextAssembler
    from tangku_agentos.ai_foundation.prompts.manager import PromptManager
    from tangku_agentos.ai_foundation.memory.connector import MemoryConnector
    from tangku_agentos.ai_foundation.knowledge.connector import KnowledgeConnector
    from tangku_agentos.ai_foundation.embeddings.manager import EmbeddingManager
    from tangku_agentos.ai_foundation.retrieval.pipeline import RetrievalPipeline
    from tangku_agentos.ai_foundation.reasoning.manager import ReasoningManager
    from tangku_agentos.ai_foundation.planning.manager import PlanningManager
    from tangku_agentos.ai_foundation.tools.manager import ToolManager
    from tangku_agentos.ai_foundation.execution.pipeline import ExecutionPipeline
    from tangku_agentos.ai_foundation.orchestration.orchestrator import MultiModelOrchestrator
    from tangku_agentos.ai_foundation.budgeting.manager import TokenBudgetManager
    from tangku_agentos.ai_foundation.caching.cache import AICache
    from tangku_agentos.ai_foundation.guardrails.manager import GuardrailManager
    from tangku_agentos.ai_foundation.monitoring.manager import MonitoringManager
    from tangku_agentos.ai_foundation.registry.model_registry import ModelRegistry
    from tangku_agentos.ai_foundation.registry.capability_registry import CapabilityRegistry
    from tangku_agentos.ai_foundation.security.manager import SecurityManager

logger = logging.getLogger(__name__)


class FoundationStatus(Enum):
    """Status of the AI Foundation."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    DEGRADED = auto()
    ERROR = auto()
    STOPPED = auto()


@dataclass
class FoundationMetrics:
    """Metrics for the AI Foundation."""
    requests_processed: int = 0
    tokens_processed: int = 0
    cost_incurred: float = 0.0
    latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    provider_errors: Dict[str, int] = field(default_factory=dict)
    model_usage: Dict[str, int] = field(default_factory=dict)
    tool_usage: Dict[str, int] = field(default_factory=dict)
    memory_retrievals: int = 0
    knowledge_retrievals: int = 0
    embedding_operations: int = 0
    retrieval_operations: int = 0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "requests_processed": self.requests_processed,
            "tokens_processed": self.tokens_processed,
            "cost_incurred": self.cost_incurred,
            "latency_ms": self.latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "provider_errors": self.provider_errors.copy(),
            "model_usage": self.model_usage.copy(),
            "tool_usage": self.tool_usage.copy(),
            "memory_retrievals": self.memory_retrievals,
            "knowledge_retrievals": self.knowledge_retrievals,
            "embedding_operations": self.embedding_operations,
            "retrieval_operations": self.retrieval_operations,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.requests_processed = 0
        self.tokens_processed = 0
        self.cost_incurred = 0.0
        self.latency_ms = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.provider_errors.clear()
        self.model_usage.clear()
        self.tool_usage.clear()
        self.memory_retrievals = 0
        self.knowledge_retrievals = 0
        self.embedding_operations = 0
        self.retrieval_operations = 0
        self.last_request_time = None
        self.last_error = None
        self.last_error_time = None


class AIFoundation:
    """
    The main class for the AI Foundation Framework.
    
    This class provides a unified interface for all AI operations while maintaining
    complete provider independence. It orchestrates all AI components and provides
    a clean abstraction layer between the Cognitive System and AI providers.
    
    Key Features:
    - Provider-agnostic AI operations
    - Model abstraction and management
    - Session and conversation management
    - Context assembly and management
    - Memory and knowledge integration
    - Tool execution and management
    - Embedding and retrieval support
    - Multi-model orchestration
    - Token budgeting and cost tracking
    - Caching and performance optimization
    - Guardrails and safety
    - Comprehensive monitoring
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import AIFoundation
        >>> 
        >>> # Initialize the foundation
        >>> foundation = AIFoundation()
        >>> 
        >>> # Register providers
        >>> await foundation.providers.register_openai(api_key="...")
        >>> await foundation.providers.register_anthropic(api_key="...")
        >>> 
        >>> # Create a session
        >>> session = await foundation.sessions.create(
        ...     model="gpt-4",
        ...     provider="openai",
        ...     context={"user": "user123"}
        ... )
        >>> 
        >>> # Execute AI request
        >>> response = await foundation.execute(
        ...     session_id=session.session_id,
        ...     prompt="Hello, how are you?",
        ...     max_tokens=100
        ... )
        >>> 
        >>> # Get metrics
        >>> metrics = foundation.get_metrics()
    """

    def __init__(self, config: Optional["AIConfig"] = None):
        """
        Initialize the AI Foundation.
        
        Args:
            config: Configuration for the AI Foundation.
        """
        self._config = config or AIConfig()
        self._status = FoundationStatus.UNINITIALIZED
        self._initialized = False
        self._started = False
        self._stopped = True
        
        # Component instances (lazy loaded)
        self._providers: Optional["ProviderRegistry"] = None
        self._sessions: Optional["SessionManager"] = None
        self._conversations: Optional["ConversationManager"] = None
        self._context_assembler: Optional["ContextAssembler"] = None
        self._prompt_manager: Optional["PromptManager"] = None
        self._memory_connector: Optional["MemoryConnector"] = None
        self._knowledge_connector: Optional["KnowledgeConnector"] = None
        self._embedding_manager: Optional["EmbeddingManager"] = None
        self._retrieval_pipeline: Optional["RetrievalPipeline"] = None
        self._reasoning_manager: Optional["ReasoningManager"] = None
        self._planning_manager: Optional["PlanningManager"] = None
        self._tool_manager: Optional["ToolManager"] = None
        self._execution_pipeline: Optional["ExecutionPipeline"] = None
        self._orchestrator: Optional["MultiModelOrchestrator"] = None
        self._budget_manager: Optional["TokenBudgetManager"] = None
        self._cache: Optional["AICache"] = None
        self._guardrails: Optional["GuardrailManager"] = None
        self._monitoring: Optional["MonitoringManager"] = None
        self._model_registry: Optional["ModelRegistry"] = None
        self._capability_registry: Optional["CapabilityRegistry"] = None
        self._security: Optional["SecurityManager"] = None
        
        # Metrics
        self._metrics = FoundationMetrics()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("AIFoundation initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def status(self) -> FoundationStatus:
        """Get the current status."""
        return self._status

    @property
    def is_initialized(self) -> bool:
        """Check if the foundation is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the foundation is started."""
        return self._started

    @property
    def is_stopped(self) -> bool:
        """Check if the foundation is stopped."""
        return self._stopped

    @property
    def metrics(self) -> FoundationMetrics:
        """Get the foundation metrics."""
        return self._metrics

    # Lazy-loaded properties
    @property
    def providers(self) -> "ProviderRegistry":
        """Get the provider registry."""
        if self._providers is None:
            from tangku_agentos.ai_foundation.providers.registry import ProviderRegistry
            self._providers = ProviderRegistry(self._config, self)
        return self._providers

    @property
    def sessions(self) -> "SessionManager":
        """Get the session manager."""
        if self._sessions is None:
            from tangku_agentos.ai_foundation.sessions.manager import SessionManager
            self._sessions = SessionManager(self._config, self)
        return self._sessions

    @property
    def conversations(self) -> "ConversationManager":
        """Get the conversation manager."""
        if self._conversations is None:
            from tangku_agentos.ai_foundation.conversations.manager import ConversationManager
            self._conversations = ConversationManager(self._config, self)
        return self._conversations

    @property
    def context(self) -> "ContextAssembler":
        """Get the context assembler."""
        if self._context_assembler is None:
            from tangku_agentos.ai_foundation.context.assembler import ContextAssembler
            self._context_assembler = ContextAssembler(self._config, self)
        return self._context_assembler

    @property
    def prompts(self) -> "PromptManager":
        """Get the prompt manager."""
        if self._prompt_manager is None:
            from tangku_agentos.ai_foundation.prompts.manager import PromptManager
            self._prompt_manager = PromptManager(self._config, self)
        return self._prompt_manager

    @property
    def memory(self) -> "MemoryConnector":
        """Get the memory connector."""
        if self._memory_connector is None:
            from tangku_agentos.ai_foundation.memory.connector import MemoryConnector
            self._memory_connector = MemoryConnector(self._config, self)
        return self._memory_connector

    @property
    def knowledge(self) -> "KnowledgeConnector":
        """Get the knowledge connector."""
        if self._knowledge_connector is None:
            from tangku_agentos.ai_foundation.knowledge.connector import KnowledgeConnector
            self._knowledge_connector = KnowledgeConnector(self._config, self)
        return self._knowledge_connector

    @property
    def embeddings(self) -> "EmbeddingManager":
        """Get the embedding manager."""
        if self._embedding_manager is None:
            from tangku_agentos.ai_foundation.embeddings.manager import EmbeddingManager
            self._embedding_manager = EmbeddingManager(self._config, self)
        return self._embedding_manager

    @property
    def retrieval(self) -> "RetrievalPipeline":
        """Get the retrieval pipeline."""
        if self._retrieval_pipeline is None:
            from tangku_agentos.ai_foundation.retrieval.pipeline import RetrievalPipeline
            self._retrieval_pipeline = RetrievalPipeline(self._config, self)
        return self._retrieval_pipeline

    @property
    def reasoning(self) -> "ReasoningManager":
        """Get the reasoning manager."""
        if self._reasoning_manager is None:
            from tangku_agentos.ai_foundation.reasoning.manager import ReasoningManager
            self._reasoning_manager = ReasoningManager(self._config, self)
        return self._reasoning_manager

    @property
    def planning(self) -> "PlanningManager":
        """Get the planning manager."""
        if self._planning_manager is None:
            from tangku_agentos.ai_foundation.planning.manager import PlanningManager
            self._planning_manager = PlanningManager(self._config, self)
        return self._planning_manager

    @property
    def tools(self) -> "ToolManager":
        """Get the tool manager."""
        if self._tool_manager is None:
            from tangku_agentos.ai_foundation.tools.manager import ToolManager
            self._tool_manager = ToolManager(self._config, self)
        return self._tool_manager

    @property
    def execution(self) -> "ExecutionPipeline":
        """Get the execution pipeline."""
        if self._execution_pipeline is None:
            from tangku_agentos.ai_foundation.execution.pipeline import ExecutionPipeline
            self._execution_pipeline = ExecutionPipeline(self._config, self)
        return self._execution_pipeline

    @property
    def orchestrator(self) -> "MultiModelOrchestrator":
        """Get the multi-model orchestrator."""
        if self._orchestrator is None:
            from tangku_agentos.ai_foundation.orchestration.orchestrator import MultiModelOrchestrator
            self._orchestrator = MultiModelOrchestrator(self._config, self)
        return self._orchestrator

    @property
    def budget(self) -> "TokenBudgetManager":
        """Get the token budget manager."""
        if self._budget_manager is None:
            from tangku_agentos.ai_foundation.budgeting.manager import TokenBudgetManager
            self._budget_manager = TokenBudgetManager(self._config, self)
        return self._budget_manager

    @property
    def cache(self) -> "AICache":
        """Get the AI cache."""
        if self._cache is None:
            from tangku_agentos.ai_foundation.caching.cache import AICache
            self._cache = AICache(self._config, self)
        return self._cache

    @property
    def guardrails(self) -> "GuardrailManager":
        """Get the guardrail manager."""
        if self._guardrails is None:
            from tangku_agentos.ai_foundation.guardrails.manager import GuardrailManager
            self._guardrails = GuardrailManager(self._config, self)
        return self._guardrails

    @property
    def monitoring(self) -> "MonitoringManager":
        """Get the monitoring manager."""
        if self._monitoring is None:
            from tangku_agentos.ai_foundation.monitoring.manager import MonitoringManager
            self._monitoring = MonitoringManager(self._config, self)
        return self._monitoring

    @property
    def models(self) -> "ModelRegistry":
        """Get the model registry."""
        if self._model_registry is None:
            from tangku_agentos.ai_foundation.registry.model_registry import ModelRegistry
            self._model_registry = ModelRegistry(self._config, self)
        return self._model_registry

    @property
    def capabilities(self) -> "CapabilityRegistry":
        """Get the capability registry."""
        if self._capability_registry is None:
            from tangku_agentos.ai_foundation.registry.capability_registry import CapabilityRegistry
            self._capability_registry = CapabilityRegistry(self._config, self)
        return self._capability_registry

    @property
    def security(self) -> "SecurityManager":
        """Get the security manager."""
        if self._security is None:
            from tangku_agentos.ai_foundation.security.manager import SecurityManager
            self._security = SecurityManager(self._config, self)
        return self._security

    async def initialize(self) -> None:
        """
        Initialize the AI Foundation.
        
        This method initializes all components and prepares the foundation
        for AI operations.
        """
        if self._initialized:
            logger.warning("AIFoundation already initialized")
            return
        
        logger.info("Initializing AIFoundation...")
        
        try:
            self._status = FoundationStatus.INITIALIZING
            
            # Initialize all components
            await self._initialize_components()
            
            # Mark as initialized
            self._initialized = True
            self._status = FoundationStatus.READY
            
            logger.info("AIFoundation initialized successfully")
            
        except Exception as e:
            self._status = FoundationStatus.ERROR
            logger.error(f"Failed to initialize AIFoundation: {e}")
            raise

    async def _initialize_components(self) -> None:
        """Initialize all components."""
        # Initialize components that need initialization
        if self._providers:
            await self._providers.initialize()
        
        if self._sessions:
            await self._sessions.initialize()
        
        if self._conversations:
            await self._conversations.initialize()
        
        if self._context_assembler:
            await self._context_assembler.initialize()
        
        if self._prompt_manager:
            await self._prompt_manager.initialize()
        
        if self._memory_connector:
            await self._memory_connector.initialize()
        
        if self._knowledge_connector:
            await self._knowledge_connector.initialize()
        
        if self._embedding_manager:
            await self._embedding_manager.initialize()
        
        if self._retrieval_pipeline:
            await self._retrieval_pipeline.initialize()
        
        if self._reasoning_manager:
            await self._reasoning_manager.initialize()
        
        if self._planning_manager:
            await self._planning_manager.initialize()
        
        if self._tool_manager:
            await self._tool_manager.initialize()
        
        if self._execution_pipeline:
            await self._execution_pipeline.initialize()
        
        if self._orchestrator:
            await self._orchestrator.initialize()
        
        if self._budget_manager:
            await self._budget_manager.initialize()
        
        if self._cache:
            await self._cache.initialize()
        
        if self._guardrails:
            await self._guardrails.initialize()
        
        if self._monitoring:
            await self._monitoring.initialize()
        
        if self._model_registry:
            await self._model_registry.initialize()
        
        if self._capability_registry:
            await self._capability_registry.initialize()
        
        if self._security:
            await self._security.initialize()

    async def start(self) -> None:
        """
        Start the AI Foundation.
        
        This method starts all components and prepares the foundation
        to process AI requests.
        """
        if self._started:
            logger.warning("AIFoundation already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting AIFoundation...")
        
        try:
            self._status = FoundationStatus.INITIALIZING
            
            # Start all components
            await self._start_components()
            
            # Mark as started
            self._started = True
            self._stopped = False
            self._status = FoundationStatus.READY
            
            logger.info("AIFoundation started successfully")
            
        except Exception as e:
            self._status = FoundationStatus.ERROR
            logger.error(f"Failed to start AIFoundation: {e}")
            raise

    async def _start_components(self) -> None:
        """Start all components."""
        # Start components that need to be started
        if self._providers:
            await self._providers.start()
        
        if self._sessions:
            await self._sessions.start()
        
        if self._conversations:
            await self._conversations.start()
        
        if self._monitoring:
            await self._monitoring.start()
        
        if self._cache:
            await self._cache.start()

    async def stop(self) -> None:
        """
        Stop the AI Foundation.
        
        This method stops all components and cleans up resources.
        """
        if self._stopped:
            logger.warning("AIFoundation already stopped")
            return
        
        logger.info("Stopping AIFoundation...")
        
        try:
            self._status = FoundationStatus.STOPPED
            
            # Stop all components
            await self._stop_components()
            
            # Mark as stopped
            self._started = False
            self._stopped = True
            
            logger.info("AIFoundation stopped successfully")
            
        except Exception as e:
            self._status = FoundationStatus.ERROR
            logger.error(f"Failed to stop AIFoundation: {e}")
            raise

    async def _stop_components(self) -> None:
        """Stop all components."""
        # Stop components in reverse order
        if self._cache:
            await self._cache.stop()
        
        if self._monitoring:
            await self._monitoring.stop()
        
        if self._conversations:
            await self._conversations.stop()
        
        if self._sessions:
            await self._sessions.stop()
        
        if self._providers:
            await self._providers.stop()

    async def execute(
        self,
        prompt: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        stop_sequences: Optional[List[str]] = None,
        stream: bool = False,
        use_cache: bool = True,
        use_memory: bool = True,
        use_knowledge: bool = True,
        use_tools: bool = True,
        use_reasoning: bool = True,
        use_planning: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute an AI request through the foundation.
        
        This is the main entry point for AI operations. It orchestrates
        the entire AI execution pipeline.
        
        Args:
            prompt: The prompt or list of messages to send to the AI.
            model: Model to use (optional, will use default).
            provider: Provider to use (optional, will use default).
            session_id: Session ID (optional, will create new session).
            conversation_id: Conversation ID (optional, will create new conversation).
            context: Additional context for the request.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p sampling.
            top_k: Top-k sampling.
            stop_sequences: Stop sequences for generation.
            stream: Whether to stream the response.
            use_cache: Whether to use caching.
            use_memory: Whether to use memory retrieval.
            use_knowledge: Whether to use knowledge retrieval.
            use_tools: Whether to use tool execution.
            use_reasoning: Whether to use reasoning.
            use_planning: Whether to use planning.
            **kwargs: Additional provider-specific parameters.
        
        Returns:
            AIResponse or AsyncGenerator[StreamChunk] if streaming.
        """
        import time
        start_time = time.time()
        
        try:
            # Update metrics
            self._metrics.requests_processed += 1
            self._metrics.last_request_time = datetime.utcnow()
            
            # Build the request
            request = self._build_request(
                prompt=prompt,
                model=model,
                provider=provider,
                session_id=session_id,
                conversation_id=conversation_id,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                stop_sequences=stop_sequences,
                stream=stream,
                use_cache=use_cache,
                use_memory=use_memory,
                use_knowledge=use_knowledge,
                use_tools=use_tools,
                use_reasoning=use_reasoning,
                use_planning=use_planning,
                **kwargs
            )
            
            # Execute through the pipeline
            if stream:
                result = self._execute_stream(request)
            else:
                result = await self._execute_single(request)
            
            # Update metrics
            self._metrics.latency_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            self._metrics.errors += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(f"AI execution failed: {e}")
            raise

    def _build_request(self, **kwargs) -> Any:
        """Build an AIRequest from the given parameters."""
        from tangku_agentos.ai_foundation.models.request import AIRequest
        from tangku_agentos.ai_foundation.models.message import Message, MessageRole
        
        # Convert prompt to messages if needed
        if isinstance(kwargs.get("prompt"), str):
            messages = [
                Message(
                    role=MessageRole.USER,
                    content=kwargs["prompt"]
                )
            ]
        else:
            messages = kwargs.get("prompt", [])
        
        return AIRequest(
            messages=messages,
            model=kwargs.get("model"),
            provider=kwargs.get("provider"),
            session_id=kwargs.get("session_id"),
            conversation_id=kwargs.get("conversation_id"),
            context=kwargs.get("context", {}),
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.9),
            top_k=kwargs.get("top_k", 50),
            stop_sequences=kwargs.get("stop_sequences"),
            stream=kwargs.get("stream", False),
            use_cache=kwargs.get("use_cache", True),
            use_memory=kwargs.get("use_memory", True),
            use_knowledge=kwargs.get("use_knowledge", True),
            use_tools=kwargs.get("use_tools", True),
            use_reasoning=kwargs.get("use_reasoning", True),
            use_planning=kwargs.get("use_planning", True),
            extra=kwargs
        )

    async def _execute_single(self, request: Any) -> Any:
        """Execute a single AI request."""
        # Execute through the execution pipeline
        return await self.execution.execute(request)

    async def _execute_stream(self, request: Any) -> Any:
        """Execute a streaming AI request."""
        # Execute through the execution pipeline with streaming
        async for chunk in self.execution.execute_stream(request):
            yield chunk

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Send a chat message through the foundation.
        
        This is a convenience method for chat-style interactions.
        
        Args:
            message: The user message.
            session_id: Session ID (optional).
            conversation_id: Conversation ID (optional).
            model: Model to use (optional).
            provider: Provider to use (optional).
            context: Additional context.
            **kwargs: Additional parameters.
        
        Returns:
            AIResponse with the assistant's reply.
        """
        # Get or create conversation
        if conversation_id:
            conversation = await self.conversations.get(conversation_id)
        else:
            conversation = await self.conversations.create(
                session_id=session_id,
                model=model,
                provider=provider
            )
            conversation_id = conversation.conversation_id
        
        # Add user message to conversation
        await self.conversations.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message
        )
        
        # Get conversation messages
        messages = await self.conversations.get_messages(conversation_id)
        
        # Execute AI request
        response = await self.execute(
            prompt=messages,
            session_id=session_id,
            conversation_id=conversation_id,
            model=model,
            provider=provider,
            context=context,
            **kwargs
        )
        
        # Add assistant message to conversation
        await self.conversations.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response.content if hasattr(response, 'content') else str(response)
        )
        
        return response

    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed.
            model: Embedding model to use.
            provider: Provider to use.
            **kwargs: Additional parameters.
        
        Returns:
            EmbeddingResult with the embedding vector.
        """
        return await self.embeddings.embed(text, model, provider, **kwargs)

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        use_memory: bool = True,
        use_knowledge: bool = True,
        **kwargs
    ) -> Any:
        """
        Retrieve information from memory and knowledge.
        
        Args:
            query: Search query.
            limit: Maximum number of results.
            use_memory: Whether to search memory.
            use_knowledge: Whether to search knowledge.
            **kwargs: Additional parameters.
        
        Returns:
            RetrievalResult with retrieved information.
        """
        return await self.retrieval.retrieve(
            query=query,
            limit=limit,
            use_memory=use_memory,
            use_knowledge=use_knowledge,
            **kwargs
        )

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments for the tool.
            session_id: Session ID (optional).
            **kwargs: Additional parameters.
        
        Returns:
            Tool execution result.
        """
        return await self.tools.execute(tool_name, arguments, session_id, **kwargs)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the AI Foundation.
        
        Returns:
            Dictionary with foundation information.
        """
        return {
            "status": self._status.name,
            "initialized": self._initialized,
            "started": self._started,
            "stopped": self._stopped,
            "providers": await self.providers.get_info() if self._providers else {},
            "sessions": await self.sessions.get_info() if self._sessions else {},
            "conversations": await self.conversations.get_info() if self._conversations else {},
            "models": await self.models.get_info() if self._models else {},
            "capabilities": await self.capabilities.get_info() if self._capabilities else {},
            "metrics": self._metrics.to_dict(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the AI Foundation.
        
        Returns:
            Dictionary with metrics.
        """
        return self._metrics.to_dict()

    async def reset(self) -> None:
        """
        Reset the AI Foundation.
        
        This method resets all components and clears all state.
        """
        logger.info("Resetting AIFoundation...")
        
        try:
            # Reset all components
            await self._reset_components()
            
            # Reset metrics
            self._metrics.reset()
            
            # Reset state
            self._initialized = False
            self._started = False
            self._stopped = True
            self._status = FoundationStatus.UNINITIALIZED
            
            logger.info("AIFoundation reset successfully")
            
        except Exception as e:
            logger.error(f"Failed to reset AIFoundation: {e}")
            raise

    async def _reset_components(self) -> None:
        """Reset all components."""
        # Reset components that need to be reset
        if self._providers:
            await self._providers.reset()
        
        if self._sessions:
            await self._sessions.reset()
        
        if self._conversations:
            await self._conversations.reset()
        
        if self._cache:
            await self._cache.reset()
        
        if self._monitoring:
            await self._monitoring.reset()

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AIFoundation("
            f"status={self._status.name}, "
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"requests={self._metrics.requests_processed})"
        )
