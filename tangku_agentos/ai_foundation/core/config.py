"""
AI Foundation Framework - Configuration

This module provides configuration classes for the AI Foundation Framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union


@dataclass
class ProviderConfig:
    """Configuration for AI providers."""
    openai: Dict[str, Any] = field(default_factory=dict)
    anthropic: Dict[str, Any] = field(default_factory=dict)
    google: Dict[str, Any] = field(default_factory=dict)
    groq: Dict[str, Any] = field(default_factory=dict)
    mistral: Dict[str, Any] = field(default_factory=dict)
    openrouter: Dict[str, Any] = field(default_factory=dict)
    ollama: Dict[str, Any] = field(default_factory=dict)
    lm_studio: Dict[str, Any] = field(default_factory=dict)
    vllm: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Default provider
    default_provider: str = "openai"
    
    # Timeout settings
    timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    retryable_errors: List[str] = field(default_factory=lambda: [
        "rate_limit", "timeout", "connection_error", "temporary_failure"
    ])
    
    # Rate limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 1000
    max_requests_per_second: int = 100
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_time: float = 60.0


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    # Default models
    default_chat_model: str = "gpt-4"
    default_completion_model: str = "gpt-4"
    default_embedding_model: str = "text-embedding-3-small"
    default_vision_model: str = "gpt-4-vision-preview"
    default_audio_model: str = "whisper-1"
    default_image_model: str = "dall-e-3"
    
    # Model aliases
    aliases: Dict[str, str] = field(default_factory=dict)
    
    # Model capabilities
    capability_check_enabled: bool = True
    fallback_models: Dict[str, List[str]] = field(default_factory=dict)
    
    # Token limits
    max_input_tokens: int = 128000
    max_output_tokens: int = 4096
    max_total_tokens: int = 131072
    
    # Temperature settings
    default_temperature: float = 0.7
    default_top_p: float = 0.9
    default_top_k: int = 50


@dataclass
class SessionConfig:
    """Configuration for AI sessions."""
    # Session settings
    max_sessions: int = 1000
    session_timeout: float = 3600.0  # 1 hour
    session_cleanup_interval: float = 300.0  # 5 minutes
    
    # Conversation settings
    max_conversations_per_session: int = 100
    conversation_timeout: float = 86400.0  # 24 hours
    conversation_cleanup_interval: float = 3600.0  # 1 hour
    
    # History settings
    max_history_length: int = 100
    history_compression_enabled: bool = True
    history_summarization_enabled: bool = True
    
    # Persistence
    persistence_enabled: bool = False
    persistence_interval: float = 60.0  # 1 minute


@dataclass
class ContextConfig:
    """Configuration for context assembly."""
    # Context sources
    include_conversation: bool = True
    include_memory: bool = True
    include_knowledge: bool = True
    include_workspace: bool = True
    include_repository: bool = True
    include_terminal: bool = True
    include_system: bool = True
    include_runtime: bool = True
    
    # Context limits
    max_context_tokens: int = 128000
    max_context_messages: int = 100
    max_context_length: int = 100000
    
    # Context assembly
    assembly_strategy: str = "auto"
    context_ranking_enabled: bool = True
    context_filtering_enabled: bool = True
    
    # Context caching
    context_cache_enabled: bool = True
    context_cache_ttl: float = 300.0  # 5 minutes


@dataclass
class MemoryConfig:
    """Configuration for memory integration."""
    # Memory settings
    enabled: bool = True
    max_memory_results: int = 10
    memory_similarity_threshold: float = 0.7
    
    # Memory types
    use_working_memory: bool = True
    use_long_term_memory: bool = True
    use_episodic_memory: bool = True
    use_semantic_memory: bool = True
    
    # Memory retrieval
    retrieval_strategy: str = "hybrid"
    rerank_results: bool = True
    max_rerank_results: int = 5


@dataclass
class KnowledgeConfig:
    """Configuration for knowledge integration."""
    # Knowledge settings
    enabled: bool = True
    max_knowledge_results: int = 10
    knowledge_similarity_threshold: float = 0.7
    
    # Knowledge retrieval
    retrieval_strategy: str = "semantic"
    use_keyword_search: bool = True
    use_semantic_search: bool = True
    use_graph_search: bool = False
    
    # Knowledge ranking
    rerank_results: bool = True
    max_rerank_results: int = 5


@dataclass
class EmbeddingConfig:
    """Configuration for embeddings."""
    # Embedding settings
    enabled: bool = True
    default_embedding_model: str = "text-embedding-3-small"
    
    # Embedding providers
    use_openai_embeddings: bool = True
    use_anthropic_embeddings: bool = False
    use_google_embeddings: bool = False
    use_custom_embeddings: bool = False
    
    # Embedding cache
    cache_enabled: bool = True
    cache_size: int = 10000
    cache_ttl: float = 86400.0  # 24 hours
    
    # Embedding batching
    batch_size: int = 100
    batch_delay: float = 0.1  # 100ms


@dataclass
class RetrievalConfig:
    """Configuration for retrieval."""
    # Retrieval settings
    enabled: bool = True
    retrieval_strategy: str = "hybrid"
    
    # Retrieval components
    use_memory_retrieval: bool = True
    use_knowledge_retrieval: bool = True
    use_embedding_search: bool = True
    use_keyword_search: bool = True
    
    # Retrieval limits
    max_retrieval_results: int = 20
    max_memory_results: int = 10
    max_knowledge_results: int = 10
    
    # Re-ranking
    rerank_enabled: bool = True
    rerank_model: str = "default"
    max_rerank_results: int = 5


@dataclass
class ToolConfig:
    """Configuration for tools."""
    # Tool settings
    enabled: bool = True
    max_concurrent_tools: int = 5
    tool_timeout: float = 30.0
    
    # Tool discovery
    auto_discover_tools: bool = True
    tool_discovery_interval: float = 60.0  # 1 minute
    
    # Tool execution
    max_tool_retries: int = 3
    tool_retry_delay: float = 1.0
    
    # Tool caching
    cache_enabled: bool = True
    cache_ttl: float = 300.0  # 5 minutes


@dataclass
class ReasoningConfig:
    """Configuration for reasoning."""
    # Reasoning settings
    enabled: bool = True
    default_reasoning_model: str = "gpt-4"
    
    # Reasoning modes
    use_chain_of_thought: bool = True
    use_tree_of_thought: bool = False
    use_graph_reasoning: bool = True
    
    # Reasoning limits
    max_reasoning_depth: int = 10
    max_reasoning_branches: int = 5
    max_reasoning_iterations: int = 100


@dataclass
class PlanningConfig:
    """Configuration for planning."""
    # Planning settings
    enabled: bool = True
    default_planning_model: str = "gpt-4"
    
    # Planning modes
    use_hierarchical_planning: bool = True
    use_parallel_planning: bool = True
    use_adaptive_planning: bool = True
    
    # Planning limits
    max_plan_depth: int = 10
    max_plan_branches: int = 5
    max_plan_length: int = 20


@dataclass
class CacheConfig:
    """Configuration for caching."""
    # Cache settings
    enabled: bool = True
    cache_backend: str = "memory"  # memory, redis, file
    
    # Cache sizes
    response_cache_size: int = 1000
    embedding_cache_size: int = 10000
    prompt_cache_size: int = 1000
    context_cache_size: int = 1000
    
    # Cache TTLs
    response_cache_ttl: float = 3600.0  # 1 hour
    embedding_cache_ttl: float = 86400.0  # 24 hours
    prompt_cache_ttl: float = 86400.0  # 24 hours
    context_cache_ttl: float = 300.0  # 5 minutes
    
    # Cache compression
    compression_enabled: bool = True
    compression_threshold: int = 1000  # Compress items larger than 1000 bytes


@dataclass
class BudgetConfig:
    """Configuration for token budgeting."""
    # Budget settings
    enabled: bool = True
    max_tokens_per_request: int = 131072
    max_tokens_per_session: int = 1000000
    max_tokens_per_user: int = 10000000
    
    # Budget strategies
    strategy: str = "auto"  # auto, strict, flexible
    compression_enabled: bool = True
    summarization_enabled: bool = True
    
    # Budget alerts
    alert_threshold: float = 0.8  # Alert when 80% of budget used
    block_threshold: float = 0.95  # Block when 95% of budget used


@dataclass
class GuardrailConfig:
    """Configuration for guardrails."""
    # Guardrail settings
    enabled: bool = True
    
    # Safety checks
    prompt_injection_detection: bool = True
    jailbreak_detection: bool = True
    sensitive_data_detection: bool = True
    
    # Content filtering
    content_filtering_enabled: bool = True
    blocked_topics: List[str] = field(default_factory=lambda: [
        "violence", "hate speech", "illegal activities", "self-harm"
    ])
    
    # Permission checks
    permission_check_enabled: bool = True
    require_authentication: bool = True
    
    # Rate limiting
    rate_limit_enabled: bool = True
    max_requests_per_user: int = 1000


@dataclass
class MonitoringConfig:
    """Configuration for monitoring."""
    # Monitoring settings
    enabled: bool = True
    
    # Metrics collection
    collect_latency: bool = True
    collect_token_usage: bool = True
    collect_cost: bool = True
    collect_errors: bool = True
    
    # Logging
    log_requests: bool = True
    log_responses: bool = False  # Don't log full responses by default
    log_errors: bool = True
    
    # Metrics backends
    metrics_backends: List[str] = field(default_factory=lambda: ["prometheus", "logging"])
    
    # Alerting
    alerting_enabled: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "latency": 1000.0,  # 1 second
        "error_rate": 0.01,  # 1%
        "cost": 100.0,  # $100
    })


@dataclass
class SecurityConfig:
    """Configuration for security."""
    # Security settings
    enabled: bool = True
    
    # API key management
    api_key_isolation: bool = True
    encrypted_secrets: bool = True
    
    # Authentication
    require_authentication: bool = True
    auth_backend: str = "jwt"  # jwt, api_key, oauth
    
    # Authorization
    permission_validation: bool = True
    role_based_access: bool = True
    
    # Audit logging
    audit_logging_enabled: bool = True
    audit_log_retention: int = 30  # 30 days


@dataclass
class IntegrationConfig:
    """Configuration for integration with other TangkuAgentOS components."""
    # Integration settings
    memory_engine_enabled: bool = True
    knowledge_engine_enabled: bool = True
    runtime_communication_enabled: bool = True
    
    # Component timeouts
    memory_timeout: float = 5.0
    knowledge_timeout: float = 5.0
    runtime_timeout: float = 5.0
    
    # Retry settings
    max_integration_retries: int = 3
    integration_retry_delay: float = 1.0


@dataclass
class AIConfig:
    """
    Main configuration for the AI Foundation Framework.
    
    This class consolidates all configuration options for the AI Foundation.
    """
    # Core settings
    name: str = "AI Foundation"
    version: str = "1.0.0"
    debug: bool = False
    
    # Provider configuration
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    
    # Model configuration
    models: ModelConfig = field(default_factory=ModelConfig)
    
    # Session configuration
    sessions: SessionConfig = field(default_factory=SessionConfig)
    
    # Context configuration
    context: ContextConfig = field(default_factory=ContextConfig)
    
    # Memory configuration
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Knowledge configuration
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    
    # Embedding configuration
    embeddings: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Retrieval configuration
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    
    # Tool configuration
    tools: ToolConfig = field(default_factory=ToolConfig)
    
    # Reasoning configuration
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    
    # Planning configuration
    planning: PlanningConfig = field(default_factory=PlanningConfig)
    
    # Cache configuration
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Budget configuration
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    
    # Guardrail configuration
    guardrails: GuardrailConfig = field(default_factory=GuardrailConfig)
    
    # Monitoring configuration
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Security configuration
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Integration configuration
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "debug": self.debug,
            "providers": self.providers.to_dict() if hasattr(self.providers, 'to_dict') else vars(self.providers),
            "models": self.models.to_dict() if hasattr(self.models, 'to_dict') else vars(self.models),
            "sessions": self.sessions.to_dict() if hasattr(self.sessions, 'to_dict') else vars(self.sessions),
            "context": self.context.to_dict() if hasattr(self.context, 'to_dict') else vars(self.context),
            "memory": self.memory.to_dict() if hasattr(self.memory, 'to_dict') else vars(self.memory),
            "knowledge": self.knowledge.to_dict() if hasattr(self.knowledge, 'to_dict') else vars(self.knowledge),
            "embeddings": self.embeddings.to_dict() if hasattr(self.embeddings, 'to_dict') else vars(self.embeddings),
            "retrieval": self.retrieval.to_dict() if hasattr(self.retrieval, 'to_dict') else vars(self.retrieval),
            "tools": self.tools.to_dict() if hasattr(self.tools, 'to_dict') else vars(self.tools),
            "reasoning": self.reasoning.to_dict() if hasattr(self.reasoning, 'to_dict') else vars(self.reasoning),
            "planning": self.planning.to_dict() if hasattr(self.planning, 'to_dict') else vars(self.planning),
            "cache": self.cache.to_dict() if hasattr(self.cache, 'to_dict') else vars(self.cache),
            "budget": self.budget.to_dict() if hasattr(self.budget, 'to_dict') else vars(self.budget),
            "guardrails": self.guardrails.to_dict() if hasattr(self.guardrails, 'to_dict') else vars(self.guardrails),
            "monitoring": self.monitoring.to_dict() if hasattr(self.monitoring, 'to_dict') else vars(self.monitoring),
            "security": self.security.to_dict() if hasattr(self.security, 'to_dict') else vars(self.security),
            "integration": self.integration.to_dict() if hasattr(self.integration, 'to_dict') else vars(self.integration),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIConfig":
        """Create configuration from dictionary."""
        # Handle nested configurations
        config_data = data.copy()
        
        if "providers" in config_data and isinstance(config_data["providers"], dict):
            config_data["providers"] = ProviderConfig(**config_data["providers"])
        if "models" in config_data and isinstance(config_data["models"], dict):
            config_data["models"] = ModelConfig(**config_data["models"])
        if "sessions" in config_data and isinstance(config_data["sessions"], dict):
            config_data["sessions"] = SessionConfig(**config_data["sessions"])
        if "context" in config_data and isinstance(config_data["context"], dict):
            config_data["context"] = ContextConfig(**config_data["context"])
        if "memory" in config_data and isinstance(config_data["memory"], dict):
            config_data["memory"] = MemoryConfig(**config_data["memory"])
        if "knowledge" in config_data and isinstance(config_data["knowledge"], dict):
            config_data["knowledge"] = KnowledgeConfig(**config_data["knowledge"])
        if "embeddings" in config_data and isinstance(config_data["embeddings"], dict):
            config_data["embeddings"] = EmbeddingConfig(**config_data["embeddings"])
        if "retrieval" in config_data and isinstance(config_data["retrieval"], dict):
            config_data["retrieval"] = RetrievalConfig(**config_data["retrieval"])
        if "tools" in config_data and isinstance(config_data["tools"], dict):
            config_data["tools"] = ToolConfig(**config_data["tools"])
        if "reasoning" in config_data and isinstance(config_data["reasoning"], dict):
            config_data["reasoning"] = ReasoningConfig(**config_data["reasoning"])
        if "planning" in config_data and isinstance(config_data["planning"], dict):
            config_data["planning"] = PlanningConfig(**config_data["planning"])
        if "cache" in config_data and isinstance(config_data["cache"], dict):
            config_data["cache"] = CacheConfig(**config_data["cache"])
        if "budget" in config_data and isinstance(config_data["budget"], dict):
            config_data["budget"] = BudgetConfig(**config_data["budget"])
        if "guardrails" in config_data and isinstance(config_data["guardrails"], dict):
            config_data["guardrails"] = GuardrailConfig(**config_data["guardrails"])
        if "monitoring" in config_data and isinstance(config_data["monitoring"], dict):
            config_data["monitoring"] = MonitoringConfig(**config_data["monitoring"])
        if "security" in config_data and isinstance(config_data["security"], dict):
            config_data["security"] = SecurityConfig(**config_data["security"])
        if "integration" in config_data and isinstance(config_data["integration"], dict):
            config_data["integration"] = IntegrationConfig(**config_data["integration"])
        
        return cls(**config_data)


def create_ai_config(**kwargs) -> AIConfig:
    """
    Create an AI configuration with sensible defaults.
    
    Args:
        **kwargs: Configuration options.
    
    Returns:
        AIConfig instance.
    """
    return AIConfig(**kwargs)
