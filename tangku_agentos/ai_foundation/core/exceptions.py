"""
AI Foundation Framework - Exceptions

This module defines custom exceptions for the AI Foundation Framework.
"""

from __future__ import annotations

from typing import Any, Optional


class AIFoundationError(Exception):
    """Base exception for AI Foundation errors."""
    
    def __init__(self, message: str = "AI Foundation error", code: str = "AI_FOUNDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Provider Exceptions

class ProviderError(AIFoundationError):
    """Base exception for provider errors."""
    
    def __init__(self, message: str = "Provider error", code: str = "PROVIDER_ERROR", provider: str = ""):
        super().__init__(message, code)
        self.provider = provider


class ProviderNotFoundError(ProviderError):
    """Exception for provider not found."""
    
    def __init__(self, provider: str):
        super().__init__(f"Provider not found: {provider}", "PROVIDER_NOT_FOUND", provider)


class ProviderNotAvailableError(ProviderError):
    """Exception for provider not available."""
    
    def __init__(self, provider: str, reason: str = ""):
        message = f"Provider not available: {provider}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "PROVIDER_NOT_AVAILABLE", provider)
        self.reason = reason


class ProviderAuthenticationError(ProviderError):
    """Exception for provider authentication failure."""
    
    def __init__(self, provider: str, reason: str = "Invalid credentials"):
        super().__init__(f"Provider authentication failed: {provider} - {reason}", "PROVIDER_AUTH_ERROR", provider)
        self.reason = reason


class ProviderRateLimitError(ProviderError):
    """Exception for provider rate limit exceeded."""
    
    def __init__(self, provider: str, retry_after: float = 0):
        message = f"Provider rate limit exceeded: {provider}"
        if retry_after > 0:
            message += f" - Retry after {retry_after} seconds"
        super().__init__(message, "PROVIDER_RATE_LIMIT", provider)
        self.retry_after = retry_after


class ProviderTimeoutError(ProviderError):
    """Exception for provider timeout."""
    
    def __init__(self, provider: str, timeout: float):
        super().__init__(f"Provider timeout: {provider} after {timeout} seconds", "PROVIDER_TIMEOUT", provider)
        self.timeout = timeout


# Model Exceptions

class ModelError(AIFoundationError):
    """Base exception for model errors."""
    
    def __init__(self, message: str = "Model error", code: str = "MODEL_ERROR", model: str = ""):
        super().__init__(message, code)
        self.model = model


class ModelNotFoundError(ModelError):
    """Exception for model not found."""
    
    def __init__(self, model: str, provider: str = ""):
        message = f"Model not found: {model}"
        if provider:
            message += f" (provider: {provider})"
        super().__init__(message, "MODEL_NOT_FOUND", model)
        self.provider = provider


class ModelNotAvailableError(ModelError):
    """Exception for model not available."""
    
    def __init__(self, model: str, provider: str = "", reason: str = ""):
        message = f"Model not available: {model}"
        if provider:
            message += f" (provider: {provider})"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "MODEL_NOT_AVAILABLE", model)
        self.provider = provider
        self.reason = reason


class ModelCapabilityError(ModelError):
    """Exception for model capability mismatch."""
    
    def __init__(self, model: str, required_capability: str, available_capabilities: list = None):
        message = f"Model {model} does not support capability: {required_capability}"
        if available_capabilities:
            message += f" - Available: {', '.join(available_capabilities)}"
        super().__init__(message, "MODEL_CAPABILITY_ERROR", model)
        self.required_capability = required_capability
        self.available_capabilities = available_capabilities or []


class ModelContextLengthError(ModelError):
    """Exception for model context length exceeded."""
    
    def __init__(self, model: str, context_length: int, max_length: int):
        super().__init__(
            f"Model {model} context length {context_length} exceeds maximum {max_length}",
            "MODEL_CONTEXT_LENGTH_ERROR",
            model
        )
        self.context_length = context_length
        self.max_length = max_length


# Session Exceptions

class SessionError(AIFoundationError):
    """Base exception for session errors."""
    
    def __init__(self, message: str = "Session error", code: str = "SESSION_ERROR", session_id: str = ""):
        super().__init__(message, code)
        self.session_id = session_id


class SessionNotFoundError(SessionError):
    """Exception for session not found."""
    
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", "SESSION_NOT_FOUND", session_id)


class SessionExpiredError(SessionError):
    """Exception for session expired."""
    
    def __init__(self, session_id: str):
        super().__init__(f"Session expired: {session_id}", "SESSION_EXPIRED", session_id)


class SessionLimitError(SessionError):
    """Exception for session limit exceeded."""
    
    def __init__(self, max_sessions: int):
        super().__init__(f"Session limit exceeded: maximum {max_sessions} sessions", "SESSION_LIMIT_ERROR")
        self.max_sessions = max_sessions


# Conversation Exceptions

class ConversationError(AIFoundationError):
    """Base exception for conversation errors."""
    
    def __init__(self, message: str = "Conversation error", code: str = "CONVERSATION_ERROR", conversation_id: str = ""):
        super().__init__(message, code)
        self.conversation_id = conversation_id


class ConversationNotFoundError(ConversationError):
    """Exception for conversation not found."""
    
    def __init__(self, conversation_id: str):
        super().__init__(f"Conversation not found: {conversation_id}", "CONVERSATION_NOT_FOUND", conversation_id)


class ConversationLimitError(ConversationError):
    """Exception for conversation limit exceeded."""
    
    def __init__(self, max_conversations: int):
        super().__init__(f"Conversation limit exceeded: maximum {max_conversations} conversations", "CONVERSATION_LIMIT_ERROR")
        self.max_conversations = max_conversations


# Context Exceptions

class ContextError(AIFoundationError):
    """Base exception for context errors."""
    
    def __init__(self, message: str = "Context error", code: str = "CONTEXT_ERROR"):
        super().__init__(message, code)


class ContextOverflowError(ContextError):
    """Exception for context overflow."""
    
    def __init__(self, context_length: int, max_length: int):
        super().__init__(
            f"Context overflow: {context_length} tokens exceeds maximum {max_length}",
            "CONTEXT_OVERFLOW"
        )
        self.context_length = context_length
        self.max_length = max_length


class ContextAssemblyError(ContextError):
    """Exception for context assembly failure."""
    
    def __init__(self, message: str = "Failed to assemble context"):
        super().__init__(message, "CONTEXT_ASSEMBLY_ERROR")


# Prompt Exceptions

class PromptError(AIFoundationError):
    """Base exception for prompt errors."""
    
    def __init__(self, message: str = "Prompt error", code: str = "PROMPT_ERROR"):
        super().__init__(message, code)


class PromptNotFoundError(PromptError):
    """Exception for prompt not found."""
    
    def __init__(self, prompt_id: str):
        super().__init__(f"Prompt not found: {prompt_id}", "PROMPT_NOT_FOUND")
        self.prompt_id = prompt_id


class PromptValidationError(PromptError):
    """Exception for prompt validation failure."""
    
    def __init__(self, message: str = "Prompt validation failed", errors: list = None):
        super().__init__(message, "PROMPT_VALIDATION_ERROR")
        self.errors = errors or []


class PromptTemplateError(PromptError):
    """Exception for prompt template rendering failure."""
    
    def __init__(self, template_id: str, error: str = ""):
        message = f"Prompt template rendering failed: {template_id}"
        if error:
            message += f" - {error}"
        super().__init__(message, "PROMPT_TEMPLATE_ERROR")
        self.template_id = template_id
        self.error = error


# Memory Exceptions

class MemoryError(AIFoundationError):
    """Base exception for memory errors."""
    
    def __init__(self, message: str = "Memory error", code: str = "MEMORY_ERROR"):
        super().__init__(message, code)


class MemoryRetrievalError(MemoryError):
    """Exception for memory retrieval failure."""
    
    def __init__(self, message: str = "Memory retrieval failed"):
        super().__init__(message, "MEMORY_RETRIEVAL_ERROR")


class MemoryStorageError(MemoryError):
    """Exception for memory storage failure."""
    
    def __init__(self, message: str = "Memory storage failed"):
        super().__init__(message, "MEMORY_STORAGE_ERROR")


# Knowledge Exceptions

class KnowledgeError(AIFoundationError):
    """Base exception for knowledge errors."""
    
    def __init__(self, message: str = "Knowledge error", code: str = "KNOWLEDGE_ERROR"):
        super().__init__(message, code)


class KnowledgeRetrievalError(KnowledgeError):
    """Exception for knowledge retrieval failure."""
    
    def __init__(self, message: str = "Knowledge retrieval failed"):
        super().__init__(message, "KNOWLEDGE_RETRIEVAL_ERROR")


# Embedding Exceptions

class EmbeddingError(AIFoundationError):
    """Base exception for embedding errors."""
    
    def __init__(self, message: str = "Embedding error", code: str = "EMBEDDING_ERROR"):
        super().__init__(message, code)


class EmbeddingGenerationError(EmbeddingError):
    """Exception for embedding generation failure."""
    
    def __init__(self, message: str = "Embedding generation failed"):
        super().__init__(message, "EMBEDDING_GENERATION_ERROR")


# Retrieval Exceptions

class RetrievalError(AIFoundationError):
    """Base exception for retrieval errors."""
    
    def __init__(self, message: str = "Retrieval error", code: str = "RETRIEVAL_ERROR"):
        super().__init__(message, code)


class RetrievalPipelineError(RetrievalError):
    """Exception for retrieval pipeline failure."""
    
    def __init__(self, message: str = "Retrieval pipeline failed"):
        super().__init__(message, "RETRIEVAL_PIPELINE_ERROR")


# Tool Exceptions

class ToolError(AIFoundationError):
    """Base exception for tool errors."""
    
    def __init__(self, message: str = "Tool error", code: str = "TOOL_ERROR", tool_name: str = ""):
        super().__init__(message, code)
        self.tool_name = tool_name


class ToolNotFoundError(ToolError):
    """Exception for tool not found."""
    
    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}", "TOOL_NOT_FOUND", tool_name)


class ToolExecutionError(ToolError):
    """Exception for tool execution failure."""
    
    def __init__(self, tool_name: str, error: str = ""):
        message = f"Tool execution failed: {tool_name}"
        if error:
            message += f" - {error}"
        super().__init__(message, "TOOL_EXECUTION_ERROR", tool_name)
        self.error = error


class ToolPermissionError(ToolError):
    """Exception for tool permission denied."""
    
    def __init__(self, tool_name: str, user: str = "", reason: str = ""):
        message = f"Tool permission denied: {tool_name}"
        if user:
            message += f" for user {user}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "TOOL_PERMISSION_ERROR", tool_name)
        self.user = user
        self.reason = reason


# Execution Exceptions

class ExecutionError(AIFoundationError):
    """Base exception for execution errors."""
    
    def __init__(self, message: str = "Execution error", code: str = "EXECUTION_ERROR"):
        super().__init__(message, code)


class ExecutionPipelineError(ExecutionError):
    """Exception for execution pipeline failure."""
    
    def __init__(self, message: str = "Execution pipeline failed", step: str = ""):
        if step:
            message = f"Execution pipeline failed at step: {step} - {message}"
        super().__init__(message, "EXECUTION_PIPELINE_ERROR")
        self.step = step


class ExecutionTimeoutError(ExecutionError):
    """Exception for execution timeout."""
    
    def __init__(self, timeout: float, step: str = ""):
        message = f"Execution timeout after {timeout} seconds"
        if step:
            message += f" at step: {step}"
        super().__init__(message, "EXECUTION_TIMEOUT_ERROR")
        self.timeout = timeout
        self.step = step


# Orchestration Exceptions

class OrchestrationError(AIFoundationError):
    """Base exception for orchestration errors."""
    
    def __init__(self, message: str = "Orchestration error", code: str = "ORCHESTRATION_ERROR"):
        super().__init__(message, code)


class NoAvailableModelError(OrchestrationError):
    """Exception for no available model."""
    
    def __init__(self, required_capabilities: list = None):
        message = "No available model"
        if required_capabilities:
            message += f" with capabilities: {', '.join(required_capabilities)}"
        super().__init__(message, "NO_AVAILABLE_MODEL")
        self.required_capabilities = required_capabilities or []


class ModelSelectionError(OrchestrationError):
    """Exception for model selection failure."""
    
    def __init__(self, message: str = "Model selection failed"):
        super().__init__(message, "MODEL_SELECTION_ERROR")


# Budget Exceptions

class BudgetError(AIFoundationError):
    """Base exception for budget errors."""
    
    def __init__(self, message: str = "Budget error", code: str = "BUDGET_ERROR"):
        super().__init__(message, code)


class BudgetExceededError(BudgetError):
    """Exception for budget exceeded."""
    
    def __init__(self, budget_type: str = "request", used: int = 0, limit: int = 0):
        super().__init__(
            f"{budget_type.capitalize()} budget exceeded: {used} > {limit}",
            "BUDGET_EXCEEDED"
        )
        self.budget_type = budget_type
        self.used = used
        self.limit = limit


class TokenLimitError(BudgetError):
    """Exception for token limit exceeded."""
    
    def __init__(self, tokens: int, limit: int):
        super().__init__(
            f"Token limit exceeded: {tokens} > {limit}",
            "TOKEN_LIMIT_ERROR"
        )
        self.tokens = tokens
        self.limit = limit


# Cache Exceptions

class CacheError(AIFoundationError):
    """Base exception for cache errors."""
    
    def __init__(self, message: str = "Cache error", code: str = "CACHE_ERROR"):
        super().__init__(message, code)


class CacheMissError(CacheError):
    """Exception for cache miss (not really an error, but useful for tracking)."""
    
    def __init__(self, key: str):
        super().__init__(f"Cache miss: {key}", "CACHE_MISS")
        self.key = key


# Guardrail Exceptions

class GuardrailError(AIFoundationError):
    """Base exception for guardrail errors."""
    
    def __init__(self, message: str = "Guardrail error", code: str = "GUARDRAIL_ERROR"):
        super().__init__(message, code)


class GuardrailViolationError(GuardrailError):
    """Exception for guardrail violation."""
    
    def __init__(self, guardrail: str, message: str = "Guardrail violated"):
        super().__init__(f"{guardrail}: {message}", "GUARDRAIL_VIOLATION")
        self.guardrail = guardrail


class PromptInjectionError(GuardrailError):
    """Exception for prompt injection detected."""
    
    def __init__(self, message: str = "Prompt injection detected"):
        super().__init__(message, "PROMPT_INJECTION")


class JailbreakError(GuardrailError):
    """Exception for jailbreak attempt detected."""
    
    def __init__(self, message: str = "Jailbreak attempt detected"):
        super().__init__(message, "JAILBREAK_ATTEMPT")


class SensitiveDataError(GuardrailError):
    """Exception for sensitive data detected."""
    
    def __init__(self, data_type: str = "unknown", message: str = "Sensitive data detected"):
        super().__init__(f"{data_type}: {message}", "SENSITIVE_DATA")
        self.data_type = data_type


# Security Exceptions

class SecurityError(AIFoundationError):
    """Base exception for security errors."""
    
    def __init__(self, message: str = "Security error", code: str = "SECURITY_ERROR"):
        super().__init__(message, code)


class AuthenticationError(SecurityError):
    """Exception for authentication failure."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(SecurityError):
    """Exception for authorization failure."""
    
    def __init__(self, message: str = "Authorization failed", user: str = "", resource: str = ""):
        if user and resource:
            message = f"Authorization failed for user {user} on resource {resource}"
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.user = user
        self.resource = resource


class PermissionError(SecurityError):
    """Exception for permission denied."""
    
    def __init__(self, message: str = "Permission denied", user: str = "", action: str = "", resource: str = ""):
        if user and action and resource:
            message = f"Permission denied for user {user} to {action} on {resource}"
        super().__init__(message, "PERMISSION_ERROR")
        self.user = user
        self.action = action
        self.resource = resource


# Integration Exceptions

class IntegrationError(AIFoundationError):
    """Base exception for integration errors."""
    
    def __init__(self, message: str = "Integration error", code: str = "INTEGRATION_ERROR", component: str = ""):
        super().__init__(message, code)
        self.component = component


class MemoryIntegrationError(IntegrationError):
    """Exception for memory integration failure."""
    
    def __init__(self, message: str = "Memory integration failed"):
        super().__init__(message, "MEMORY_INTEGRATION_ERROR", "memory")


class KnowledgeIntegrationError(IntegrationError):
    """Exception for knowledge integration failure."""
    
    def __init__(self, message: str = "Knowledge integration failed"):
        super().__init__(message, "KNOWLEDGE_INTEGRATION_ERROR", "knowledge")


class RuntimeIntegrationError(IntegrationError):
    """Exception for runtime integration failure."""
    
    def __init__(self, message: str = "Runtime integration failed"):
        super().__init__(message, "RUNTIME_INTEGRATION_ERROR", "runtime")


# Export all exceptions
__all__ = [
    # Base
    "AIFoundationError",
    # Provider
    "ProviderError", "ProviderNotFoundError", "ProviderNotAvailableError",
    "ProviderAuthenticationError", "ProviderRateLimitError", "ProviderTimeoutError",
    # Model
    "ModelError", "ModelNotFoundError", "ModelNotAvailableError",
    "ModelCapabilityError", "ModelContextLengthError",
    # Session
    "SessionError", "SessionNotFoundError", "SessionExpiredError", "SessionLimitError",
    # Conversation
    "ConversationError", "ConversationNotFoundError", "ConversationLimitError",
    # Context
    "ContextError", "ContextOverflowError", "ContextAssemblyError",
    # Prompt
    "PromptError", "PromptNotFoundError", "PromptValidationError", "PromptTemplateError",
    # Memory
    "MemoryError", "MemoryRetrievalError", "MemoryStorageError",
    # Knowledge
    "KnowledgeError", "KnowledgeRetrievalError",
    # Embedding
    "EmbeddingError", "EmbeddingGenerationError",
    # Retrieval
    "RetrievalError", "RetrievalPipelineError",
    # Tool
    "ToolError", "ToolNotFoundError", "ToolExecutionError", "ToolPermissionError",
    # Execution
    "ExecutionError", "ExecutionPipelineError", "ExecutionTimeoutError",
    # Orchestration
    "OrchestrationError", "NoAvailableModelError", "ModelSelectionError",
    # Budget
    "BudgetError", "BudgetExceededError", "TokenLimitError",
    # Cache
    "CacheError", "CacheMissError",
    # Guardrail
    "GuardrailError", "GuardrailViolationError", "PromptInjectionError",
    "JailbreakError", "SensitiveDataError",
    # Security
    "SecurityError", "AuthenticationError", "AuthorizationError", "PermissionError",
    # Integration
    "IntegrationError", "MemoryIntegrationError", "KnowledgeIntegrationError",
    "RuntimeIntegrationError",
]
