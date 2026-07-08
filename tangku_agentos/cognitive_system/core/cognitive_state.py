"""
AI Cognitive System - Cognitive State

This module provides state management for the AI Cognitive System.
It tracks the current state of cognitive processes and maintains
context across cognitive operations.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig

logger = logging.getLogger(__name__)


class CognitiveStateEnum(Enum):
    """
    States for cognitive processes.
    
    Attributes:
        UNINITIALIZED: Cognitive system not initialized.
        INITIALIZING: Cognitive system is initializing.
        IDLE: Cognitive system is idle, waiting for input.
        PERCEIVING: Cognitive system is perceiving input.
        UNDERSTANDING: Cognitive system is understanding context.
        RETRIEVING_MEMORY: Cognitive system is retrieving memory.
        RETRIEVING_KNOWLEDGE: Cognitive system is retrieving knowledge.
        REASONING: Cognitive system is reasoning.
        PLANNING: Cognitive system is planning.
        DECIDING: Cognitive system is making a decision.
        EXECUTING: Cognitive system is executing actions.
        OBSERVING: Cognitive system is observing results.
        REFLECTING: Cognitive system is reflecting.
        LEARNING: Cognitive system is learning.
        UPDATING_MEMORY: Cognitive system is updating memory.
        PAUSED: Cognitive system is paused.
        STOPPING: Cognitive system is stopping.
        STOPPED: Cognitive system is stopped.
        ERROR: Cognitive system encountered an error.
        RECOVERING: Cognitive system is recovering from an error.
    """

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    IDLE = auto()
    PERCEIVING = auto()
    UNDERSTANDING = auto()
    RETRIEVING_MEMORY = auto()
    RETRIEVING_KNOWLEDGE = auto()
    REASONING = auto()
    PLANNING = auto()
    DECIDING = auto()
    EXECUTING = auto()
    OBSERVING = auto()
    REFLECTING = auto()
    LEARNING = auto()
    UPDATING_MEMORY = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
    RECOVERING = auto()


class CognitiveStage(Enum):
    """
    Stages in the cognitive loop.
    
    The cognitive loop follows this sequence:
    PERCEIVE -> UNDERSTAND_CONTEXT -> RETRIEVE_MEMORY -> RETRIEVE_KNOWLEDGE ->
    REASON -> PLAN -> EVALUATE_OPTIONS -> SELECT_TOOLS -> EXECUTE ->
    OBSERVE_RESULTS -> REFLECT -> LEARN -> UPDATE_MEMORY -> CONTINUE
    """

    PERCEIVE = auto()
    UNDERSTAND_CONTEXT = auto()
    RETRIEVE_MEMORY = auto()
    RETRIEVE_KNOWLEDGE = auto()
    REASON = auto()
    PLAN = auto()
    EVALUATE_OPTIONS = auto()
    SELECT_TOOLS = auto()
    EXECUTE = auto()
    OBSERVE_RESULTS = auto()
    REFLECT = auto()
    LEARN = auto()
    UPDATE_MEMORY = auto()
    CONTINUE = auto()


@dataclass
class CognitiveMetrics:
    """
    Metrics for cognitive processes.
    
    Attributes:
        stage_times: Time spent in each cognitive stage.
        stage_counts: Number of times each stage was executed.
        total_processing_time: Total time spent in cognitive processing.
        total_iterations: Total number of cognitive iterations.
        memory_retrievals: Number of memory retrieval operations.
        knowledge_retrievals: Number of knowledge retrieval operations.
        reasoning_operations: Number of reasoning operations.
        planning_operations: Number of planning operations.
        decision_operations: Number of decision operations.
        execution_operations: Number of execution operations.
        reflection_operations: Number of reflection operations.
        learning_operations: Number of learning operations.
        memory_updates: Number of memory update operations.
        errors: Number of errors encountered.
        last_error: Last error encountered.
        last_error_time: Time of last error.
    """

    stage_times: Dict[str, float] = field(default_factory=dict)
    stage_counts: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    total_iterations: int = 0
    memory_retrievals: int = 0
    knowledge_retrievals: int = 0
    reasoning_operations: int = 0
    planning_operations: int = 0
    decision_operations: int = 0
    execution_operations: int = 0
    reflection_operations: int = 0
    learning_operations: int = 0
    memory_updates: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def record_stage_start(self, stage: CognitiveStage) -> None:
        """Record the start of a cognitive stage."""
        stage_name = stage.name
        if stage_name not in self.stage_times:
            self.stage_times[stage_name] = 0.0
            self.stage_counts[stage_name] = 0

    def record_stage_end(self, stage: CognitiveStage, duration: float) -> None:
        """Record the end of a cognitive stage."""
        stage_name = stage.name
        self.stage_times[stage_name] += duration
        self.stage_counts[stage_name] += 1
        self.total_processing_time += duration

    def record_iteration(self) -> None:
        """Record a cognitive iteration."""
        self.total_iterations += 1

    def record_memory_retrieval(self) -> None:
        """Record a memory retrieval operation."""
        self.memory_retrievals += 1

    def record_knowledge_retrieval(self) -> None:
        """Record a knowledge retrieval operation."""
        self.knowledge_retrievals += 1

    def record_reasoning_operation(self) -> None:
        """Record a reasoning operation."""
        self.reasoning_operations += 1

    def record_planning_operation(self) -> None:
        """Record a planning operation."""
        self.planning_operations += 1

    def record_decision_operation(self) -> None:
        """Record a decision operation."""
        self.decision_operations += 1

    def record_execution_operation(self) -> None:
        """Record an execution operation."""
        self.execution_operations += 1

    def record_reflection_operation(self) -> None:
        """Record a reflection operation."""
        self.reflection_operations += 1

    def record_learning_operation(self) -> None:
        """Record a learning operation."""
        self.learning_operations += 1

    def record_memory_update(self) -> None:
        """Record a memory update operation."""
        self.memory_updates += 1

    def record_error(self, error: str) -> None:
        """Record an error."""
        self.errors += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary."""
        return {
            "stage_times": self.stage_times.copy(),
            "stage_counts": self.stage_counts.copy(),
            "total_processing_time": self.total_processing_time,
            "total_iterations": self.total_iterations,
            "memory_retrievals": self.memory_retrievals,
            "knowledge_retrievals": self.knowledge_retrievals,
            "reasoning_operations": self.reasoning_operations,
            "planning_operations": self.planning_operations,
            "decision_operations": self.decision_operations,
            "execution_operations": self.execution_operations,
            "reflection_operations": self.reflection_operations,
            "learning_operations": self.learning_operations,
            "memory_updates": self.memory_updates,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.stage_times.clear()
        self.stage_counts.clear()
        self.total_processing_time = 0.0
        self.total_iterations = 0
        self.memory_retrievals = 0
        self.knowledge_retrievals = 0
        self.reasoning_operations = 0
        self.planning_operations = 0
        self.decision_operations = 0
        self.execution_operations = 0
        self.reflection_operations = 0
        self.learning_operations = 0
        self.memory_updates = 0
        self.errors = 0
        self.last_error = None
        self.last_error_time = None


@dataclass
class CognitiveContext:
    """
    Context for cognitive processes.
    
    This class maintains the context across cognitive operations,
    including conversation history, current goals, and relevant information.
    
    Attributes:
        conversation_id: Unique identifier for the conversation.
        session_id: Unique identifier for the session.
        user_id: Identifier for the user.
        agent_id: Identifier for the agent.
        current_goal: Current goal being pursued.
        sub_goals: Sub-goals being pursued.
        conversation_history: History of the conversation.
        current_input: Current input being processed.
        current_output: Current output being generated.
        relevant_memories: Memories relevant to the current context.
        relevant_knowledge: Knowledge relevant to the current context.
        attention_focus: Current focus of attention.
        execution_context: Context for action execution.
        metadata: Additional metadata.
    """

    conversation_id: str = ""
    session_id: str = ""
    user_id: str = ""
    agent_id: str = ""
    current_goal: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_input: Optional[Dict[str, Any]] = None
    current_output: Optional[Dict[str, Any]] = None
    relevant_memories: List[Dict[str, Any]] = field(default_factory=list)
    relevant_knowledge: List[Dict[str, Any]] = field(default_factory=list)
    attention_focus: List[str] = field(default_factory=list)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_to_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the conversation history."""
        self.conversation_history.append(entry)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history[-limit:]

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()

    def set_goal(self, goal: str, sub_goals: List[str] = None) -> None:
        """Set the current goal and sub-goals."""
        self.current_goal = goal
        self.sub_goals = sub_goals or []

    def clear_goal(self) -> None:
        """Clear the current goal and sub-goals."""
        self.current_goal = None
        self.sub_goals.clear()

    def add_relevant_memory(self, memory: Dict[str, Any]) -> None:
        """Add a relevant memory."""
        self.relevant_memories.append(memory)

    def add_relevant_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """Add relevant knowledge."""
        self.relevant_knowledge.append(knowledge)

    def clear_relevant_info(self) -> None:
        """Clear relevant memories and knowledge."""
        self.relevant_memories.clear()
        self.relevant_knowledge.clear()

    def set_focus(self, focus_items: List[str]) -> None:
        """Set the current focus of attention."""
        self.attention_focus = focus_items

    def clear_focus(self) -> None:
        """Clear the current focus of attention."""
        self.attention_focus.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "current_goal": self.current_goal,
            "sub_goals": self.sub_goals,
            "conversation_history": self.conversation_history,
            "current_input": self.current_input,
            "current_output": self.current_output,
            "relevant_memories": self.relevant_memories,
            "relevant_knowledge": self.relevant_knowledge,
            "attention_focus": self.attention_focus,
            "execution_context": self.execution_context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveContext":
        """Create context from dictionary."""
        return cls(
            conversation_id=data.get("conversation_id", ""),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            agent_id=data.get("agent_id", ""),
            current_goal=data.get("current_goal"),
            sub_goals=data.get("sub_goals", []),
            conversation_history=data.get("conversation_history", []),
            current_input=data.get("current_input"),
            current_output=data.get("current_output"),
            relevant_memories=data.get("relevant_memories", []),
            relevant_knowledge=data.get("relevant_knowledge", []),
            attention_focus=data.get("attention_focus", []),
            execution_context=data.get("execution_context", {}),
            metadata=data.get("metadata", {}),
        )


class CognitiveState:
    """
    State management for the AI Cognitive System.
    
    This class manages the state of cognitive processes, including:
    - Current state of the cognitive system
    - Current stage in the cognitive loop
    - Context across cognitive operations
    - Metrics for cognitive processes
    - Lifecycle management
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.cognitive_system.core import CognitiveState
        >>> 
        >>> state = CognitiveState()
        >>> state.set_state(CognitiveStateEnum.IDLE)
        >>> state.set_stage(CognitiveStage.PERCEIVE)
        >>> state.context.set_goal("solve_problem")
        >>> 
        >>> # Record stage timing
        >>> state.metrics.record_stage_start(CognitiveStage.PERCEIVE)
        >>> # ... processing ...
        >>> state.metrics.record_stage_end(CognitiveStage.PERCEIVE, 0.5)
    """

    def __init__(self, config: Optional["CognitiveConfig"] = None):
        """
        Initialize the cognitive state.
        
        Args:
            config: Cognitive configuration.
        """
        self._config = config
        self._state = CognitiveStateEnum.UNINITIALIZED
        self._stage = CognitiveStage.CONTINUE
        self._context = CognitiveContext()
        self._metrics = CognitiveMetrics()
        self._lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._stage_lock = asyncio.Lock()
        
        # State change callbacks
        self._on_state_change: List[Any] = []
        self._on_stage_change: List[Any] = []
        
        logger.info("CognitiveState initialized")

    @property
    def config(self) -> Optional["CognitiveConfig"]:
        """Get the cognitive configuration."""
        return self._config

    @config.setter
    def config(self, value: "CognitiveConfig") -> None:
        """Set the cognitive configuration."""
        self._config = value

    @property
    def state(self) -> CognitiveStateEnum:
        """Get the current cognitive state."""
        return self._state

    @property
    def stage(self) -> CognitiveStage:
        """Get the current cognitive stage."""
        return self._stage

    @property
    def context(self) -> CognitiveContext:
        """Get the cognitive context."""
        return self._context

    @property
    def metrics(self) -> CognitiveMetrics:
        """Get the cognitive metrics."""
        return self._metrics

    def on_state_change(self, callback: Any) -> None:
        """
        Register a callback for state changes.
        
        Args:
            callback: Callback function to call when state changes.
        """
        self._on_state_change.append(callback)

    def on_stage_change(self, callback: Any) -> None:
        """
        Register a callback for stage changes.
        
        Args:
            callback: Callback function to call when stage changes.
        """
        self._on_stage_change.append(callback)

    async def set_state(self, new_state: CognitiveStateEnum) -> None:
        """
        Set the cognitive state.
        
        Args:
            new_state: New state to set.
        """
        async with self._state_lock:
            old_state = self._state
            self._state = new_state
            
            # Call state change callbacks
            for callback in self._on_state_change:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_state, new_state)
                    else:
                        callback(old_state, new_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")
            
            logger.debug(f"Cognitive state changed: {old_state.name} -> {new_state.name}")

    async def set_stage(self, new_stage: CognitiveStage) -> None:
        """
        Set the cognitive stage.
        
        Args:
            new_stage: New stage to set.
        """
        async with self._stage_lock:
            old_stage = self._stage
            self._stage = new_stage
            
            # Call stage change callbacks
            for callback in self._on_stage_change:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(old_stage, new_stage)
                    else:
                        callback(old_stage, new_stage)
                except Exception as e:
                    logger.error(f"Error in stage change callback: {e}")
            
            logger.debug(f"Cognitive stage changed: {old_stage.name} -> {new_stage.name}")

    async def transition_to(self, new_state: CognitiveStateEnum, new_stage: CognitiveStage) -> None:
        """
        Transition to a new state and stage.
        
        Args:
            new_state: New state to set.
            new_stage: New stage to set.
        """
        await self.set_state(new_state)
        await self.set_stage(new_stage)

    async def initialize(self) -> None:
        """Initialize the cognitive state."""
        await self.set_state(CognitiveStateEnum.INITIALIZING)
        await self.set_stage(CognitiveStage.PERCEIVE)
        logger.info("Cognitive state initialized")

    async def start(self) -> None:
        """Start the cognitive state."""
        await self.set_state(CognitiveStateEnum.IDLE)
        await self.set_stage(CognitiveStage.PERCEIVE)
        logger.info("Cognitive state started")

    async def pause(self) -> None:
        """Pause the cognitive state."""
        await self.set_state(CognitiveStateEnum.PAUSED)
        logger.info("Cognitive state paused")

    async def resume(self) -> None:
        """Resume the cognitive state."""
        await self.set_state(CognitiveStateEnum.IDLE)
        logger.info("Cognitive state resumed")

    async def stop(self) -> None:
        """Stop the cognitive state."""
        await self.set_state(CognitiveStateEnum.STOPPING)
        await self.set_stage(CognitiveStage.CONTINUE)
        await self.set_state(CognitiveStateEnum.STOPPED)
        logger.info("Cognitive state stopped")

    async def set_error(self, error: str) -> None:
        """Set the cognitive state to error."""
        await self.set_state(CognitiveStateEnum.ERROR)
        self.metrics.record_error(error)
        logger.error(f"Cognitive error: {error}")

    async def recover(self) -> None:
        """Recover from an error."""
        await self.set_state(CognitiveStateEnum.RECOVERING)
        await self.set_state(CognitiveStateEnum.IDLE)
        logger.info("Cognitive state recovered")

    async def record_stage_execution(
        self,
        stage: CognitiveStage,
        duration: float,
    ) -> None:
        """
        Record the execution of a cognitive stage.
        
        Args:
            stage: The cognitive stage that was executed.
            duration: Time taken to execute the stage in seconds.
        """
        self.metrics.record_stage_start(stage)
        self.metrics.record_stage_end(stage, duration)
        self.metrics.record_iteration()

    def get_state_info(self) -> Dict[str, Any]:
        """
        Get information about the current state.
        
        Returns:
            Dictionary with state information.
        """
        return {
            "state": self._state.name,
            "stage": self._stage.name,
            "context": self._context.to_dict(),
            "metrics": self._metrics.get_metrics(),
        }

    def reset(self) -> None:
        """Reset the cognitive state."""
        self._state = CognitiveStateEnum.UNINITIALIZED
        self._stage = CognitiveStage.CONTINUE
        self._context = CognitiveContext()
        self._metrics.reset()
        logger.info("Cognitive state reset")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CognitiveState("
            f"state={self._state.name}, "
            f"stage={self._stage.name}, "
            f"iterations={self._metrics.total_iterations})"
        )
