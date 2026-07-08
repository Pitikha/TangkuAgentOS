"""
TangkuAgentOS Agent Runtime - Exception Definitions

This module defines all custom exceptions for the Agent Runtime.

Exception Hierarchy:
- AgentError (base exception)
  ├── AgentNotFoundError
  ├── AgentAlreadyExistsError
  ├── AgentLifecycleError
  ├── AgentPermissionError
  ├── AgentExecutionError
  ├── AgentCommunicationError
  ├── AgentSchedulingError
  ├── AgentRecoveryError
  ├── AgentConfigurationError
  ├── AgentMemoryError
  ├── AgentKnowledgeError
  ├── AgentPlanningError
  ├── AgentReasoningError
  ├── AgentToolError
  └── AgentSkillError

All exceptions include:
- Detailed error messages
- Agent ID (when applicable)
- Task ID (when applicable)
- Timestamp
- Error code
- Original exception (when wrapped)

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.agent_runtime.types import (
        AgentID,
        TaskID,
        SkillID,
        ToolID,
        MemoryID,
        KnowledgeID,
        PlanID,
        ReasoningID,
    )


class AgentError(Exception):
    """
    Base exception for all Agent Runtime errors.
    
    This is the root exception class for all agent-related errors.
    All other agent exceptions inherit from this class.
    
    Attributes:
        message: Human-readable error message.
        agent_id: ID of the agent (if applicable).
        task_id: ID of the task (if applicable).
        code: Error code for categorization.
        timestamp: When the error occurred.
        details: Additional error details.
        cause: Original exception that caused this error.
    """

    def __init__(
        self,
        message: str,
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        code: str = "AGENT_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message.
            agent_id: ID of the agent (if applicable).
            task_id: ID of the task (if applicable).
            code: Error code for categorization.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.agent_id = agent_id
        self.task_id = task_id
        self.code = code
        self.timestamp = datetime.utcnow()
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation."""
        parts = [f"AgentError({self.code})"]
        if self.agent_id:
            parts.append(f"agent_id={self.agent_id}")
        if self.task_id:
            parts.append(f"task_id={self.task_id}")
        parts.append(f"message={self.message}")
        if self.details:
            parts.append(f"details={self.details}")
        if self.cause:
            parts.append(f"cause={type(self.cause).__name__}: {self.cause}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"code={self.code}, "
            f"agent_id={self.agent_id}, "
            f"task_id={self.task_id}, "
            f"message={self.message!r}, "
            f"timestamp={self.timestamp.isoformat()}, "
            f"details={self.details}, "
            f"cause={self.cause})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary.
        
        Returns:
            Dictionary representation of the exception.
        """
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "cause": str(self.cause) if self.cause else None,
        }


# =============================================================================
# AGENT EXCEPTIONS
# =============================================================================

class AgentNotFoundError(AgentError):
    """
    Exception raised when an agent is not found.
    
    This is raised when trying to access or operate on an agent that doesn't exist.
    """

    def __init__(
        self,
        message: str = "Agent not found",
        agent_id: Optional["AgentID"] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent that was not found.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_NOT_FOUND",
            **kwargs,
        )


class AgentAlreadyExistsError(AgentError):
    """
    Exception raised when an agent already exists.
    
    This is raised when trying to create an agent with an ID that already exists.
    """

    def __init__(
        self,
        message: str = "Agent already exists",
        agent_id: Optional["AgentID"] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent that already exists.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_ALREADY_EXISTS",
            **kwargs,
        )


class AgentLifecycleError(AgentError):
    """
    Exception raised when there's an error in the agent lifecycle.
    
    This is raised when an agent cannot transition between states.
    """

    def __init__(
        self,
        message: str = "Agent lifecycle error",
        agent_id: Optional["AgentID"] = None,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            from_state: State the agent was trying to transition from.
            to_state: State the agent was trying to transition to.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "from_state": from_state,
            "to_state": to_state,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_LIFECYCLE_ERROR",
            details=details,
            **kwargs,
        )


class AgentPermissionError(AgentError):
    """
    Exception raised when an agent doesn't have permission to perform an action.
    
    This is raised when an agent tries to perform an action it's not authorized for.
    """

    def __init__(
        self,
        message: str = "Agent permission denied",
        agent_id: Optional["AgentID"] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            action: Action the agent was trying to perform.
            resource: Resource the agent was trying to access.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "action": action,
            "resource": resource,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_PERMISSION_ERROR",
            details=details,
            **kwargs,
        )


class AgentExecutionError(AgentError):
    """
    Exception raised when there's an error during agent execution.
    
    This is raised when an agent fails to execute a task or operation.
    """

    def __init__(
        self,
        message: str = "Agent execution error",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task being executed.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="AGENT_EXECUTION_ERROR",
            details=details,
            **kwargs,
        )


class AgentCommunicationError(AgentError):
    """
    Exception raised when there's an error in agent communication.
    
    This is raised when an agent fails to send or receive a message.
    """

    def __init__(
        self,
        message: str = "Agent communication error",
        agent_id: Optional["AgentID"] = None,
        target_agent_id: Optional["AgentID"] = None,
        message_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent sending the message.
            target_agent_id: ID of the agent receiving the message.
            message_type: Type of message.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "target_agent_id": target_agent_id,
            "message_type": message_type,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_COMMUNICATION_ERROR",
            details=details,
            **kwargs,
        )


class AgentSchedulingError(AgentError):
    """
    Exception raised when there's an error in agent scheduling.
    
    This is raised when a task cannot be scheduled or executed.
    """

    def __init__(
        self,
        message: str = "Agent scheduling error",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task.
            reason: Reason for the scheduling error.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "reason": reason,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="AGENT_SCHEDULING_ERROR",
            details=details,
            **kwargs,
        )


class AgentRecoveryError(AgentError):
    """
    Exception raised when there's an error during agent recovery.
    
    This is raised when an agent cannot be recovered from a failed state.
    """

    def __init__(
        self,
        message: str = "Agent recovery error",
        agent_id: Optional["AgentID"] = None,
        recovery_type: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            recovery_type: Type of recovery being attempted.
            error: Original error that triggered recovery.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "recovery_type": recovery_type,
            "original_error": error,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_RECOVERY_ERROR",
            details=details,
            **kwargs,
        )


class AgentConfigurationError(AgentError):
    """
    Exception raised when there's an error in agent configuration.
    
    This is raised when an agent's configuration is invalid or missing.
    """

    def __init__(
        self,
        message: str = "Agent configuration error",
        agent_id: Optional["AgentID"] = None,
        config_errors: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            config_errors: Dictionary of configuration errors.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "config_errors": config_errors,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_CONFIGURATION_ERROR",
            details=details,
            **kwargs,
        )


# =============================================================================
# COMPONENT EXCEPTIONS
# =============================================================================

class AgentMemoryError(AgentError):
    """
    Exception raised when there's an error with agent memory.
    """

    def __init__(
        self,
        message: str = "Agent memory error",
        agent_id: Optional["AgentID"] = None,
        memory_id: Optional["MemoryID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            memory_id: ID of the memory entry.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "memory_id": memory_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_MEMORY_ERROR",
            details=details,
            **kwargs,
        )


class AgentKnowledgeError(AgentError):
    """
    Exception raised when there's an error with agent knowledge.
    """

    def __init__(
        self,
        message: str = "Agent knowledge error",
        agent_id: Optional["AgentID"] = None,
        knowledge_id: Optional["KnowledgeID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            knowledge_id: ID of the knowledge entry.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "knowledge_id": knowledge_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_KNOWLEDGE_ERROR",
            details=details,
            **kwargs,
        )


class AgentPlanningError(AgentError):
    """
    Exception raised when there's an error with agent planning.
    """

    def __init__(
        self,
        message: str = "Agent planning error",
        agent_id: Optional["AgentID"] = None,
        plan_id: Optional["PlanID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            plan_id: ID of the plan.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "plan_id": plan_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_PLANNING_ERROR",
            details=details,
            **kwargs,
        )


class AgentReasoningError(AgentError):
    """
    Exception raised when there's an error with agent reasoning.
    """

    def __init__(
        self,
        message: str = "Agent reasoning error",
        agent_id: Optional["AgentID"] = None,
        reasoning_id: Optional["ReasoningID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            reasoning_id: ID of the reasoning session.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "reasoning_id": reasoning_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_REASONING_ERROR",
            details=details,
            **kwargs,
        )


class AgentToolError(AgentError):
    """
    Exception raised when there's an error with agent tools.
    """

    def __init__(
        self,
        message: str = "Agent tool error",
        agent_id: Optional["AgentID"] = None,
        tool_id: Optional["ToolID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            tool_id: ID of the tool.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "tool_id": tool_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_TOOL_ERROR",
            details=details,
            **kwargs,
        )


class AgentSkillError(AgentError):
    """
    Exception raised when there's an error with agent skills.
    """

    def __init__(
        self,
        message: str = "Agent skill error",
        agent_id: Optional["AgentID"] = None,
        skill_id: Optional["SkillID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            skill_id: ID of the skill.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "skill_id": skill_id,
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="AGENT_SKILL_ERROR",
            details=details,
            **kwargs,
        )


# =============================================================================
# TASK EXCEPTIONS
# =============================================================================

class TaskNotFoundError(AgentError):
    """
    Exception raised when a task is not found.
    """

    def __init__(
        self,
        message: str = "Task not found",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task that was not found.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="TASK_NOT_FOUND",
            **kwargs,
        )


class TaskAlreadyExistsError(AgentError):
    """
    Exception raised when a task already exists.
    """

    def __init__(
        self,
        message: str = "Task already exists",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task that already exists.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="TASK_ALREADY_EXISTS",
            **kwargs,
        )


class TaskExecutionError(AgentError):
    """
    Exception raised when there's an error executing a task.
    """

    def __init__(
        self,
        message: str = "Task execution error",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        error: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task.
            error: Original error message.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "original_error": error,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="TASK_EXECUTION_ERROR",
            details=details,
            **kwargs,
        )


class TaskTimeoutError(AgentError):
    """
    Exception raised when a task times out.
    """

    def __init__(
        self,
        message: str = "Task timeout",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task.
            timeout: Timeout value in seconds.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "timeout": timeout,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="TASK_TIMEOUT",
            details=details,
            **kwargs,
        )


class TaskCancelledError(AgentError):
    """
    Exception raised when a task is cancelled.
    """

    def __init__(
        self,
        message: str = "Task cancelled",
        agent_id: Optional["AgentID"] = None,
        task_id: Optional["TaskID"] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            task_id: ID of the task.
            reason: Reason for cancellation.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "reason": reason,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            code="TASK_CANCELLED",
            details=details,
            **kwargs,
        )


# =============================================================================
# SCHEDULER EXCEPTIONS
# =============================================================================

class SchedulerError(AgentError):
    """
    Exception raised when there's an error in the scheduler.
    """

    def __init__(
        self,
        message: str = "Scheduler error",
        agent_id: Optional["AgentID"] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="SCHEDULER_ERROR",
            **kwargs,
        )


class SchedulerFullError(SchedulerError):
    """
    Exception raised when the scheduler is full.
    """

    def __init__(
        self,
        message: str = "Scheduler full",
        agent_id: Optional["AgentID"] = None,
        max_tasks: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            max_tasks: Maximum number of tasks allowed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "max_tasks": max_tasks,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="SCHEDULER_FULL",
            details=details,
            **kwargs,
        )


class SchedulerBusyError(SchedulerError):
    """
    Exception raised when the scheduler is busy.
    """

    def __init__(
        self,
        message: str = "Scheduler busy",
        agent_id: Optional["AgentID"] = None,
        current_tasks: Optional[int] = None,
        max_parallel: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            current_tasks: Number of current tasks.
            max_parallel: Maximum parallel tasks allowed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "current_tasks": current_tasks,
            "max_parallel": max_parallel,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="SCHEDULER_BUSY",
            details=details,
            **kwargs,
        )


# =============================================================================
# REGISTRY EXCEPTIONS
# =============================================================================

class RegistryError(AgentError):
    """
    Exception raised when there's an error in the registry.
    """

    def __init__(
        self,
        message: str = "Registry error",
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            code="REGISTRY_ERROR",
            **kwargs,
        )


class RegistryFullError(RegistryError):
    """
    Exception raised when the registry is full.
    """

    def __init__(
        self,
        message: str = "Registry full",
        max_agents: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            max_agents: Maximum number of agents allowed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "max_agents": max_agents,
        })
        super().__init__(
            message=message,
            code="REGISTRY_FULL",
            details=details,
            **kwargs,
        )


# =============================================================================
# COMMUNICATION EXCEPTIONS
# =============================================================================

class CommunicationTimeoutError(AgentError):
    """
    Exception raised when agent communication times out.
    """

    def __init__(
        self,
        message: str = "Communication timeout",
        agent_id: Optional["AgentID"] = None,
        target_agent_id: Optional["AgentID"] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent sending the message.
            target_agent_id: ID of the agent receiving the message.
            timeout: Timeout value in seconds.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "target_agent_id": target_agent_id,
            "timeout": timeout,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="COMMUNICATION_TIMEOUT",
            details=details,
            **kwargs,
        )


class MessageDeliveryError(AgentError):
    """
    Exception raised when a message cannot be delivered.
    """

    def __init__(
        self,
        message: str = "Message delivery error",
        agent_id: Optional["AgentID"] = None,
        target_agent_id: Optional["AgentID"] = None,
        message_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent sending the message.
            target_agent_id: ID of the agent receiving the message.
            message_id: ID of the message.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "target_agent_id": target_agent_id,
            "message_id": message_id,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="MESSAGE_DELIVERY_ERROR",
            details=details,
            **kwargs,
        )


# =============================================================================
# PERSISTENCE EXCEPTIONS
# =============================================================================

class PersistenceError(AgentError):
    """
    Exception raised when there's an error with persistence.
    """

    def __init__(
        self,
        message: str = "Persistence error",
        agent_id: Optional["AgentID"] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            operation: Operation that failed.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "operation": operation,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="PERSISTENCE_ERROR",
            details=details,
            **kwargs,
        )


class PersistenceNotAvailableError(PersistenceError):
    """
    Exception raised when persistence is not available.
    """

    def __init__(
        self,
        message: str = "Persistence not available",
        agent_id: Optional["AgentID"] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            reason: Reason persistence is not available.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "reason": reason,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="PERSISTENCE_NOT_AVAILABLE",
            details=details,
            **kwargs,
        )


# =============================================================================
# INTEGRATION EXCEPTIONS
# =============================================================================

class IntegrationError(AgentError):
    """
    Exception raised when there's an error with runtime integration.
    """

    def __init__(
        self,
        message: str = "Integration error",
        agent_id: Optional["AgentID"] = None,
        runtime: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            runtime: Runtime that failed to integrate.
            **kwargs: Additional arguments.
        """
        details = kwargs.pop("details", {})
        details.update({
            "runtime": runtime,
        })
        super().__init__(
            message=message,
            agent_id=agent_id,
            code="INTEGRATION_ERROR",
            details=details,
            **kwargs,
        )


class RuntimeNotAvailableError(IntegrationError):
    """
    Exception raised when a required runtime is not available.
    """

    def __init__(
        self,
        message: str = "Runtime not available",
        agent_id: Optional["AgentID"] = None,
        runtime: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message.
            agent_id: ID of the agent.
            runtime: Runtime that is not available.
            **kwargs: Additional arguments.
        """
        super().__init__(
            message=message,
            agent_id=agent_id,
            runtime=runtime,
            code="RUNTIME_NOT_AVAILABLE",
            **kwargs,
        )
