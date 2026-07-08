#!/usr/bin/env python3
"""
TangkuAgentOS Reasoning Runtime.

This package provides a production-grade Reasoning Engine for AI agents,
supporting advanced reasoning patterns, multi-step planning, tool-assisted
reasoning, and multi-agent collaboration.

## Features
- Chain of Thought, Tree of Thoughts, Graph of Thoughts
- Reflection, self-critique, and verification
- Multi-step planning and iterative reasoning
- Multi-model reasoning with automatic fallback
- Tool-assisted reasoning with validation
- Evidence-based reasoning with citation
- Multi-agent collaboration (debate, voting, consensus)
- Performance optimization (async, parallel, streaming)
- Security features (permission-aware, audit logging)

## Usage
```python
from tangku_agentos.reasoning_runtime import ReasoningManager, ReasoningMode

# Initialize the reasoning manager
reasoning_manager = ReasoningManager()

# Create a reasoning session
session = reasoning_manager.create_session(
    context_id="task_123",
    mode=ReasoningMode.CHAIN_OF_THOUGHT,
)

# Execute reasoning
result = await reasoning_manager.reason(
    session_id=session.session_id,
    query="How do I solve this complex problem?",
    available_tools=["search", "calculate", "analyze"],
)

# Get the reasoning trace
trace = reasoning_manager.get_reasoning_trace(session_id)
for step in trace.steps:
    print(f"Step {step.step_id}: {step.content}")
```
"""

# --- Core Components ---
from .manager import ReasoningManager
from .pipeline import ReasoningPipeline, BaseReasoningPipeline
from .registry import ReasoningRegistry
from .history import ReasoningHistory, ReasoningHistoryManager

# --- Models and Types ---
from .models import (
    ReasoningContext,
    ReasoningSession,
    ReasoningMetadata,
    ReasoningStep,
    ReasoningTrace,
    ReasoningDecision,
    ReasoningMode,
    ReasoningStrategy,
    ReasoningState,
    ReasoningStatistics,
    ReasoningConfig,
    ReasoningResult,
    ReasoningPlan,
    ReasoningVerification,
    ReasoningReflection,
    ReasoningCollaboration,
    ReasoningToolCall,
    ReasoningToolResult,
    ReasoningQuery,
    ReasoningParameters,
)

# --- Exceptions ---
from .exceptions import (
    ReasoningError,
    ReasoningNotFoundError,
    ReasoningExistsError,
    ReasoningTimeoutError,
    ReasoningValidationError,
    ReasoningPermissionError,
    ReasoningExecutionError,
    ReasoningPipelineError,
    ReasoningToolError,
    ReasoningModelError,
    ReasoningProviderError,
)

# --- Interfaces ---
from .interfaces import (
    IReasoningManager,
    IReasoningPipeline,
    IReasoningRegistry,
    IReasoningHistory,
    IReasoningStrategy,
    IReasoningPlanner,
    IReasoningVerifier,
    IReasoningReflector,
    IReasoningCollaborator,
)

# --- Strategies ---
from .strategies import (
    ChainOfThoughtStrategy,
    TreeOfThoughtsStrategy,
    GraphOfThoughtsStrategy,
    ReflectiveStrategy,
    SelfCritiqueStrategy,
    VerificationStrategy,
    PlanningStrategy,
    IterativeStrategy,
    MultiModelStrategy,
    ToolAssistedStrategy,
    EvidenceBasedStrategy,
    ConstraintSolvingStrategy,
    GoalOrientedStrategy,
)

# --- Planners ---
from .planner import (
    ReasoningPlanner,
    StepByStepPlanner,
    HierarchicalPlanner,
    ParallelPlanner,
    AdaptivePlanner,
)

# --- Verifiers ---
from .verifier import (
    ReasoningVerifier,
    ConfidenceVerifier,
    ConsistencyVerifier,
    FactCheckingVerifier,
    MultiModelVerifier,
)

# --- Reflectors ---
from .reflector import (
    ReasoningReflector,
    SelfReflector,
    MultiAgentReflector,
    FeedbackReflector,
)

# --- Collaborators ---
from .collaborator import (
    ReasoningCollaborator,
    DebateCollaborator,
    VotingCollaborator,
    ConsensusCollaborator,
    ExpertDelegationCollaborator,
)

# --- Public API ---
__all__ = [
    # Core Components
    "ReasoningManager",
    "ReasoningPipeline",
    "BaseReasoningPipeline",
    "ReasoningRegistry",
    "ReasoningHistory",
    "ReasoningHistoryManager",
    # Models and Types
    "ReasoningContext",
    "ReasoningSession",
    "ReasoningMetadata",
    "ReasoningStep",
    "ReasoningTrace",
    "ReasoningDecision",
    "ReasoningMode",
    "ReasoningStrategy",
    "ReasoningState",
    "ReasoningStatistics",
    "ReasoningConfig",
    "ReasoningResult",
    "ReasoningPlan",
    "ReasoningVerification",
    "ReasoningReflection",
    "ReasoningCollaboration",
    "ReasoningToolCall",
    "ReasoningToolResult",
    "ReasoningQuery",
    "ReasoningParameters",
    # Exceptions
    "ReasoningError",
    "ReasoningNotFoundError",
    "ReasoningExistsError",
    "ReasoningTimeoutError",
    "ReasoningValidationError",
    "ReasoningPermissionError",
    "ReasoningExecutionError",
    "ReasoningPipelineError",
    "ReasoningToolError",
    "ReasoningModelError",
    "ReasoningProviderError",
    # Interfaces
    "IReasoningManager",
    "IReasoningPipeline",
    "IReasoningRegistry",
    "IReasoningHistory",
    "IReasoningStrategy",
    "IReasoningPlanner",
    "IReasoningVerifier",
    "IReasoningReflector",
    "IReasoningCollaborator",
    # Strategies
    "ChainOfThoughtStrategy",
    "TreeOfThoughtsStrategy",
    "GraphOfThoughtsStrategy",
    "ReflectiveStrategy",
    "SelfCritiqueStrategy",
    "VerificationStrategy",
    "PlanningStrategy",
    "IterativeStrategy",
    "MultiModelStrategy",
    "ToolAssistedStrategy",
    "EvidenceBasedStrategy",
    "ConstraintSolvingStrategy",
    "GoalOrientedStrategy",
    # Planners
    "ReasoningPlanner",
    "StepByStepPlanner",
    "HierarchicalPlanner",
    "ParallelPlanner",
    "AdaptivePlanner",
    # Verifiers
    "ReasoningVerifier",
    "ConfidenceVerifier",
    "ConsistencyVerifier",
    "FactCheckingVerifier",
    "MultiModelVerifier",
    # Reflectors
    "ReasoningReflector",
    "SelfReflector",
    "MultiAgentReflector",
    "FeedbackReflector",
    # Collaborators
    "ReasoningCollaborator",
    "DebateCollaborator",
    "VotingCollaborator",
    "ConsensusCollaborator",
    "ExpertDelegationCollaborator",
]
