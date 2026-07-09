"""
AI Foundation Framework for TangkuAgentOS.

This framework provides a universal abstraction layer between the Cognitive System
and all AI providers, memory systems, knowledge systems, tools, and execution environments.
"""

from .models import (
    AIModel,
    ChatModel,
    EmbeddingModel,
    VisionModel,
    AudioModel,
    StructuredOutputModel,
)
from .providers import (
    BaseProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenRouterProvider,
    OllamaProvider,
    TogetherAIProvider,
    CohereProvider,
    AzureOpenAIProvider,
    VertexAIProvider,
    AWSBedrockProvider,
    HuggingFaceProvider,
    CustomProvider,
)
from .sessions import SessionManager
from .conversations import ConversationManager
from .context import ContextAssembler
from .memory import MemoryConnector
from .knowledge import KnowledgeConnector
from .reasoning import ReasoningEngine
from .planning import PlanningEngine
from .embeddings import EmbeddingRegistry
from .retrieval import RetrievalPipeline
from .orchestration import MultiModelOrchestrator
from .tools import ToolExecutor
from .execution import ExecutionPipeline
from .streaming import StreamingManager
from .validation import OutputValidator
from .guardrails import GuardrailEngine
from .monitoring import MetricsCollector
from .caching import ResponseCache
from .budgeting import TokenBudgetManager
from .registry import ModelRegistry, ProviderRegistry, CapabilityRegistry
from .capabilities import CapabilityDeclarer
from .security import APIKeyIsolator, EncryptedSecretsManager
from .serialization import RequestSerializer, ResponseSerializer
from .integration import KernelIntegration, MemoryIntegration, KnowledgeIntegration

__all__ = [
    # Models
    "AIModel",
    "ChatModel",
    "EmbeddingModel",
    "VisionModel",
    "AudioModel",
    "StructuredOutputModel",
    # Providers
    "BaseProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "GroqProvider",
    "MistralProvider",
    "OpenRouterProvider",
    "OllamaProvider",
    "TogetherAIProvider",
    "CohereProvider",
    "AzureOpenAIProvider",
    "VertexAIProvider",
    "AWSBedrockProvider",
    "HuggingFaceProvider",
    "CustomProvider",
    # Sessions
    "SessionManager",
    # Conversations
    "ConversationManager",
    # Context
    "ContextAssembler",
    # Memory
    "MemoryConnector",
    # Knowledge
    "KnowledgeConnector",
    # Reasoning
    "ReasoningEngine",
    # Planning
    "PlanningEngine",
    # Embeddings
    "EmbeddingRegistry",
    # Retrieval
    "RetrievalPipeline",
    # Orchestration
    "MultiModelOrchestrator",
    # Tools
    "ToolExecutor",
    # Execution
    "ExecutionPipeline",
    # Streaming
    "StreamingManager",
    # Validation
    "OutputValidator",
    # Guardrails
    "GuardrailEngine",
    # Monitoring
    "MetricsCollector",
    # Caching
    "ResponseCache",
    # Budgeting
    "TokenBudgetManager",
    # Registry
    "ModelRegistry",
    "ProviderRegistry",
    "CapabilityRegistry",
    # Capabilities
    "CapabilityDeclarer",
    # Security
    "APIKeyIsolator",
    "EncryptedSecretsManager",
    # Serialization
    "RequestSerializer",
    "ResponseSerializer",
    # Integration
    "KernelIntegration",
    "MemoryIntegration",
    "KnowledgeIntegration",
]
