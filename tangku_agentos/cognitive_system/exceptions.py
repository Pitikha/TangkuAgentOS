"""
AI Cognitive System - Exceptions

This module defines custom exceptions for the AI Cognitive System.
Each cognitive module has its own exception hierarchy.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from typing import Any, Optional


class CognitiveError(Exception):
    """Base exception for cognitive system errors."""
    
    def __init__(self, message: str = "Cognitive system error", code: str = "COGNITIVE_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# Perception Exceptions

class PerceptionError(CognitiveError):
    """Base exception for perception errors."""
    
    def __init__(self, message: str = "Perception error", code: str = "PERCEPTION_ERROR"):
        super().__init__(message, code)


class InputParsingError(PerceptionError):
    """Exception for input parsing errors."""
    
    def __init__(self, message: str = "Failed to parse input", input_type: str = ""):
        super().__init__(f"{message}: {input_type}", "INPUT_PARSING_ERROR")
        self.input_type = input_type


class UnsupportedInputTypeError(PerceptionError):
    """Exception for unsupported input types."""
    
    def __init__(self, input_type: str):
        super().__init__(f"Unsupported input type: {input_type}", "UNSUPPORTED_INPUT_TYPE")
        self.input_type = input_type


class InputValidationError(PerceptionError):
    """Exception for input validation errors."""
    
    def __init__(self, message: str = "Input validation failed", errors: list = None):
        super().__init__(message, "INPUT_VALIDATION_ERROR")
        self.errors = errors or []


# Attention Exceptions

class AttentionError(CognitiveError):
    """Base exception for attention errors."""
    
    def __init__(self, message: str = "Attention error", code: str = "ATTENTION_ERROR"):
        super().__init__(message, code)


class FocusError(AttentionError):
    """Exception for focus errors."""
    
    def __init__(self, message: str = "Failed to focus attention"):
        super().__init__(message, "FOCUS_ERROR")


class PriorityError(AttentionError):
    """Exception for priority calculation errors."""
    
    def __init__(self, message: str = "Failed to calculate priority"):
        super().__init__(message, "PRIORITY_ERROR")


# Context Exceptions

class ContextError(CognitiveError):
    """Base exception for context errors."""
    
    def __init__(self, message: str = "Context error", code: str = "CONTEXT_ERROR"):
        super().__init__(message, code)


class ContextNotFoundError(ContextError):
    """Exception for missing context."""
    
    def __init__(self, context_type: str, context_id: str = ""):
        message = f"Context not found: {context_type}"
        if context_id:
            message += f" (ID: {context_id})"
        super().__init__(message, "CONTEXT_NOT_FOUND")
        self.context_type = context_type
        self.context_id = context_id


class ContextUpdateError(ContextError):
    """Exception for context update errors."""
    
    def __init__(self, message: str = "Failed to update context"):
        super().__init__(message, "CONTEXT_UPDATE_ERROR")


# Memory Exceptions

class MemoryError(CognitiveError):
    """Base exception for memory errors."""
    
    def __init__(self, message: str = "Memory error", code: str = "MEMORY_ERROR"):
        super().__init__(message, code)


class MemoryNotFoundError(MemoryError):
    """Exception for memory not found."""
    
    def __init__(self, memory_id: str):
        super().__init__(f"Memory not found: {memory_id}", "MEMORY_NOT_FOUND")
        self.memory_id = memory_id


class MemoryFullError(MemoryError):
    """Exception for memory full."""
    
    def __init__(self, memory_type: str = "working"):
        super().__init__(f"{memory_type} memory is full", "MEMORY_FULL")
        self.memory_type = memory_type


class MemoryRetrievalError(MemoryError):
    """Exception for memory retrieval errors."""
    
    def __init__(self, message: str = "Failed to retrieve memory"):
        super().__init__(message, "MEMORY_RETRIEVAL_ERROR")


class MemoryUpdateError(MemoryError):
    """Exception for memory update errors."""
    
    def __init__(self, message: str = "Failed to update memory"):
        super().__init__(message, "MEMORY_UPDATE_ERROR")


# Knowledge Exceptions

class KnowledgeError(CognitiveError):
    """Base exception for knowledge errors."""
    
    def __init__(self, message: str = "Knowledge error", code: str = "KNOWLEDGE_ERROR"):
        super().__init__(message, code)


class KnowledgeNotFoundError(KnowledgeError):
    """Exception for knowledge not found."""
    
    def __init__(self, knowledge_id: str = ""):
        message = "Knowledge not found"
        if knowledge_id:
            message += f": {knowledge_id}"
        super().__init__(message, "KNOWLEDGE_NOT_FOUND")
        self.knowledge_id = knowledge_id


class KnowledgeRetrievalError(KnowledgeError):
    """Exception for knowledge retrieval errors."""
    
    def __init__(self, message: str = "Failed to retrieve knowledge"):
        super().__init__(message, "KNOWLEDGE_RETRIEVAL_ERROR")


class KnowledgeUpdateError(KnowledgeError):
    """Exception for knowledge update errors."""
    
    def __init__(self, message: str = "Failed to update knowledge"):
        super().__init__(message, "KNOWLEDGE_UPDATE_ERROR")


# Reasoning Exceptions

class ReasoningError(CognitiveError):
    """Base exception for reasoning errors."""
    
    def __init__(self, message: str = "Reasoning error", code: str = "REASONING_ERROR"):
        super().__init__(message, code)


class ReasoningTimeoutError(ReasoningError):
    """Exception for reasoning timeout."""
    
    def __init__(self, timeout: float):
        super().__init__(f"Reasoning timeout after {timeout} seconds", "REASONING_TIMEOUT")
        self.timeout = timeout


class ReasoningDepthError(ReasoningError):
    """Exception for reasoning depth exceeded."""
    
    def __init__(self, max_depth: int, current_depth: int):
        super().__init__(
            f"Reasoning depth exceeded: {current_depth} > {max_depth}",
            "REASONING_DEPTH_EXCEEDED"
        )
        self.max_depth = max_depth
        self.current_depth = current_depth


class ReasoningBranchError(ReasoningError):
    """Exception for reasoning branch limit exceeded."""
    
    def __init__(self, max_branches: int, current_branches: int):
        super().__init__(
            f"Reasoning branch limit exceeded: {current_branches} > {max_branches}",
            "REASONING_BRANCH_LIMIT_EXCEEDED"
        )
        self.max_branches = max_branches
        self.current_branches = current_branches


class ReasoningIterationError(ReasoningError):
    """Exception for reasoning iteration limit exceeded."""
    
    def __init__(self, max_iterations: int, current_iterations: int):
        super().__init__(
            f"Reasoning iteration limit exceeded: {current_iterations} > {max_iterations}",
            "REASONING_ITERATION_LIMIT_EXCEEDED"
        )
        self.max_iterations = max_iterations
        self.current_iterations = current_iterations


# Planning Exceptions

class PlanningError(CognitiveError):
    """Base exception for planning errors."""
    
    def __init__(self, message: str = "Planning error", code: str = "PLANNING_ERROR"):
        super().__init__(message, code)


class PlanningTimeoutError(PlanningError):
    """Exception for planning timeout."""
    
    def __init__(self, timeout: float):
        super().__init__(f"Planning timeout after {timeout} seconds", "PLANNING_TIMEOUT")
        self.timeout = timeout


class PlanningDepthError(PlanningError):
    """Exception for planning depth exceeded."""
    
    def __init__(self, max_depth: int, current_depth: int):
        super().__init__(
            f"Planning depth exceeded: {current_depth} > {max_depth}",
            "PLANNING_DEPTH_EXCEEDED"
        )
        self.max_depth = max_depth
        self.current_depth = current_depth


class NoValidPlanError(PlanningError):
    """Exception for no valid plan found."""
    
    def __init__(self, goal: str = ""):
        message = "No valid plan found"
        if goal:
            message += f" for goal: {goal}"
        super().__init__(message, "NO_VALID_PLAN")
        self.goal = goal


# Decision Exceptions

class DecisionError(CognitiveError):
    """Base exception for decision errors."""
    
    def __init__(self, message: str = "Decision error", code: str = "DECISION_ERROR"):
        super().__init__(message, code)


class DecisionTimeoutError(DecisionError):
    """Exception for decision timeout."""
    
    def __init__(self, timeout: float):
        super().__init__(f"Decision timeout after {timeout} seconds", "DECISION_TIMEOUT")
        self.timeout = timeout


class NoOptionsError(DecisionError):
    """Exception for no options available."""
    
    def __init__(self, message: str = "No options available for decision"):
        super().__init__(message, "NO_OPTIONS")


class PermissionDeniedError(DecisionError):
    """Exception for permission denied."""
    
    def __init__(self, permission: str, action: str = ""):
        message = f"Permission denied: {permission}"
        if action:
            message += f" for action: {action}"
        super().__init__(message, "PERMISSION_DENIED")
        self.permission = permission
        self.action = action


class ResourceUnavailableError(DecisionError):
    """Exception for resource unavailable."""
    
    def __init__(self, resource: str, action: str = ""):
        message = f"Resource unavailable: {resource}"
        if action:
            message += f" for action: {action}"
        super().__init__(message, "RESOURCE_UNAVAILABLE")
        self.resource = resource
        self.action = action


# Execution Exceptions

class ExecutionError(CognitiveError):
    """Base exception for execution errors."""
    
    def __init__(self, message: str = "Execution error", code: str = "EXECUTION_ERROR"):
        super().__init__(message, code)


class ActionExecutionError(ExecutionError):
    """Exception for action execution errors."""
    
    def __init__(self, action: str, error: str = ""):
        message = f"Failed to execute action: {action}"
        if error:
            message += f" - {error}"
        super().__init__(message, "ACTION_EXECUTION_ERROR")
        self.action = action
        self.error = error


class ToolNotFoundError(ExecutionError):
    """Exception for tool not found."""
    
    def __init__(self, tool_id: str):
        super().__init__(f"Tool not found: {tool_id}", "TOOL_NOT_FOUND")
        self.tool_id = tool_id


class SkillNotFoundError(ExecutionError):
    """Exception for skill not found."""
    
    def __init__(self, skill_id: str):
        super().__init__(f"Skill not found: {skill_id}", "SKILL_NOT_FOUND")
        self.skill_id = skill_id


class MaxConcurrentActionsError(ExecutionError):
    """Exception for maximum concurrent actions exceeded."""
    
    def __init__(self, max_actions: int, current_actions: int):
        super().__init__(
            f"Maximum concurrent actions exceeded: {current_actions} > {max_actions}",
            "MAX_CONCURRENT_ACTIONS_EXCEEDED"
        )
        self.max_actions = max_actions
        self.current_actions = current_actions


# Evaluation Exceptions

class EvaluationError(CognitiveError):
    """Base exception for evaluation errors."""
    
    def __init__(self, message: str = "Evaluation error", code: str = "EVALUATION_ERROR"):
        super().__init__(message, code)


class ConfidenceCalculationError(EvaluationError):
    """Exception for confidence calculation errors."""
    
    def __init__(self, message: str = "Failed to calculate confidence"):
        super().__init__(message, "CONFIDENCE_CALCULATION_ERROR")


class OutcomeEvaluationError(EvaluationError):
    """Exception for outcome evaluation errors."""
    
    def __init__(self, message: str = "Failed to evaluate outcome"):
        super().__init__(message, "OUTCOME_EVALUATION_ERROR")


# Learning Exceptions

class LearningError(CognitiveError):
    """Base exception for learning errors."""
    
    def __init__(self, message: str = "Learning error", code: str = "LEARNING_ERROR"):
        super().__init__(message, code)


class LearningRateError(LearningError):
    """Exception for learning rate errors."""
    
    def __init__(self, message: str = "Invalid learning rate"):
        super().__init__(message, "LEARNING_RATE_ERROR")


class MemoryLearningError(LearningError):
    """Exception for memory learning errors."""
    
    def __init__(self, message: str = "Failed to learn from memory"):
        super().__init__(message, "MEMORY_LEARNING_ERROR")


class PatternLearningError(LearningError):
    """Exception for pattern learning errors."""
    
    def __init__(self, message: str = "Failed to learn pattern"):
        super().__init__(message, "PATTERN_LEARNING_ERROR")


# Confidence Exceptions

class ConfidenceError(CognitiveError):
    """Base exception for confidence errors."""
    
    def __init__(self, message: str = "Confidence error", code: str = "CONFIDENCE_ERROR"):
        super().__init__(message, code)


class LowConfidenceError(ConfidenceError):
    """Exception for low confidence."""
    
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            f"Confidence too low: {confidence:.2f} < {threshold:.2f}",
            "LOW_CONFIDENCE"
        )
        self.confidence = confidence
        self.threshold = threshold


# Monitoring Exceptions

class MonitoringError(CognitiveError):
    """Base exception for monitoring errors."""
    
    def __init__(self, message: str = "Monitoring error", code: str = "MONITORING_ERROR"):
        super().__init__(message, code)


class SelfEvaluationError(MonitoringError):
    """Exception for self-evaluation errors."""
    
    def __init__(self, message: str = "Failed to perform self-evaluation"):
        super().__init__(message, "SELF_EVALUATION_ERROR")


class SelfCorrectionError(MonitoringError):
    """Exception for self-correction errors."""
    
    def __init__(self, message: str = "Failed to perform self-correction"):
        super().__init__(message, "SELF_CORRECTION_ERROR")


# Meta-Cognition Exceptions

class MetaCognitionError(CognitiveError):
    """Base exception for meta-cognition errors."""
    
    def __init__(self, message: str = "Meta-cognition error", code: str = "META_COGNITION_ERROR"):
        super().__init__(message, code)


class StrategySelectionError(MetaCognitionError):
    """Exception for strategy selection errors."""
    
    def __init__(self, message: str = "Failed to select strategy"):
        super().__init__(message, "STRATEGY_SELECTION_ERROR")


class CognitiveFlexibilityError(MetaCognitionError):
    """Exception for cognitive flexibility errors."""
    
    def __init__(self, message: str = "Failed to adjust cognitive flexibility"):
        super().__init__(message, "COGNITIVE_FLEXIBILITY_ERROR")


# Agent Exceptions

class AgentError(CognitiveError):
    """Base exception for agent errors."""
    
    def __init__(self, message: str = "Agent error", code: str = "AGENT_ERROR"):
        super().__init__(message, code)


class AgentNotInitializedError(AgentError):
    """Exception for agent not initialized."""
    
    def __init__(self, agent_id: str = ""):
        message = "Agent not initialized"
        if agent_id:
            message += f": {agent_id}"
        super().__init__(message, "AGENT_NOT_INITIALIZED")
        self.agent_id = agent_id


class AgentNotStartedError(AgentError):
    """Exception for agent not started."""
    
    def __init__(self, agent_id: str = ""):
        message = "Agent not started"
        if agent_id:
            message += f": {agent_id}"
        super().__init__(message, "AGENT_NOT_STARTED")
        self.agent_id = agent_id


class AgentStoppedError(AgentError):
    """Exception for agent stopped."""
    
    def __init__(self, agent_id: str = ""):
        message = "Agent is stopped"
        if agent_id:
            message += f": {agent_id}"
        super().__init__(message, "AGENT_STOPPED")
        self.agent_id = agent_id


class ModuleNotAvailableError(AgentError):
    """Exception for module not available."""
    
    def __init__(self, module_name: str, agent_id: str = ""):
        message = f"Module not available: {module_name}"
        if agent_id:
            message += f" (agent: {agent_id})"
        super().__init__(message, "MODULE_NOT_AVAILABLE")
        self.module_name = module_name
        self.agent_id = agent_id


# Export all exceptions
__all__ = [
    # Base
    "CognitiveError",
    # Perception
    "PerceptionError", "InputParsingError", "UnsupportedInputTypeError", "InputValidationError",
    # Attention
    "AttentionError", "FocusError", "PriorityError",
    # Context
    "ContextError", "ContextNotFoundError", "ContextUpdateError",
    # Memory
    "MemoryError", "MemoryNotFoundError", "MemoryFullError", "MemoryRetrievalError", "MemoryUpdateError",
    # Knowledge
    "KnowledgeError", "KnowledgeNotFoundError", "KnowledgeRetrievalError", "KnowledgeUpdateError",
    # Reasoning
    "ReasoningError", "ReasoningTimeoutError", "ReasoningDepthError", "ReasoningBranchError", "ReasoningIterationError",
    # Planning
    "PlanningError", "PlanningTimeoutError", "PlanningDepthError", "NoValidPlanError",
    # Decision
    "DecisionError", "DecisionTimeoutError", "NoOptionsError", "PermissionDeniedError", "ResourceUnavailableError",
    # Execution
    "ExecutionError", "ActionExecutionError", "ToolNotFoundError", "SkillNotFoundError", "MaxConcurrentActionsError",
    # Evaluation
    "EvaluationError", "ConfidenceCalculationError", "OutcomeEvaluationError",
    # Learning
    "LearningError", "LearningRateError", "MemoryLearningError", "PatternLearningError",
    # Confidence
    "ConfidenceError", "LowConfidenceError",
    # Monitoring
    "MonitoringError", "SelfEvaluationError", "SelfCorrectionError",
    # Meta-Cognition
    "MetaCognitionError", "StrategySelectionError", "CognitiveFlexibilityError",
    # Agent
    "AgentError", "AgentNotInitializedError", "AgentNotStartedError", "AgentStoppedError", "ModuleNotAvailableError",
]
