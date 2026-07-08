"""
TangkuAgentOS - AI Cognitive System

The AI Cognitive System is the "brain" of every agent inside TangkuAgentOS.
It provides a production-grade cognitive architecture that enables agents to:
- Think, reason, learn, remember, plan, adapt, reflect, and make decisions autonomously

Architecture:
- 20+ independent cognitive modules
- Continuous cognitive loop
- Deep integration with Memory Engine and Knowledge Engine
- Production-ready implementation

Core Modules:
- Perception Engine: Multi-modal input processing
- Attention Engine: Intelligent prioritization
- Context Engine: Multi-layered context management
- Working Memory: Short-term memory storage
- Long-Term Memory Interface: LTM integration
- Episodic Memory Interface: Event memory
- Semantic Memory Interface: Concept memory
- Knowledge Interface: Knowledge Engine integration
- Reasoning Engine: Multi-mode reasoning
- Planning Engine: Goal decomposition and planning
- Reflection Engine: Self-improvement
- Decision Engine: Action selection
- Goal Manager: Goal management
- Learning Engine: Continuous learning
- Skill Selection Engine: Capability matching
- Tool Selection Engine: Tool matching
- Action Executor: Action execution
- Evaluation Engine: Outcome assessment
- Confidence Engine: Confidence estimation
- Self-Monitoring Engine: Operational awareness
- Meta-Cognition Engine: Higher-order thinking

Cognitive Loop:
Perceive → Understand Context → Retrieve Memory → Retrieve Knowledge →
Reason → Plan → Evaluate Options → Select Tools → Execute → Observe Results →
Reflect → Learn → Update Memory → Continue

Example usage:
    from tangku_agentos.cognitive_system import (
        CognitiveAgent,
        CognitiveConfig,
        CognitiveState,
        CognitiveLoop,
        CognitiveProfile,
    )
    
    # Create a cognitive agent
    agent = CognitiveAgent(
        agent_id="my_agent",
        config=CognitiveConfig(
            reasoning_mode="analytical",
            memory_enabled=True,
            knowledge_enabled=True,
            learning_enabled=True,
        )
    )
    
    # Initialize the agent
    await agent.initialize()
    
    # Process input through the cognitive loop
    response = await agent.process(input_data)
"""

# Cognitive Core
from tangku_agentos.cognitive_system.core.cognitive_agent import CognitiveAgent
from tangku_agentos.cognitive_system.core.cognitive_config import (
    CognitiveConfig,
    MemoryConfig,
    KnowledgeConfig,
    ReasoningConfig,
    PlanningConfig,
    DecisionConfig,
    AttentionConfig,
    LearningConfig,
    ExecutionConfig,
    EvaluationConfig,
    MonitoringConfig,
    MetaCognitionConfig,
    ReasoningMode,
    MemoryStrategy,
    KnowledgeStrategy,
    LearningStrategy,
    DecisionStrategy,
    PlanningStrategy,
    AttentionStrategy,
    create_cognitive_config,
)
from tangku_agentos.cognitive_system.core.cognitive_state import (
    CognitiveState,
    CognitiveStateEnum,
    CognitiveStage,
    CognitiveMetrics,
    CognitiveContext,
)
from tangku_agentos.cognitive_system.core.cognitive_loop import (
    CognitiveLoop,
    LoopMode,
    LoopStatus,
    LoopMetrics,
    LoopHooks,
)
from tangku_agentos.cognitive_system.core.cognitive_profile import (
    CognitiveProfile,
    ANALYTICAL_PROFILE,
    CREATIVE_PROFILE,
    RESEARCH_PROFILE,
    CODING_PROFILE,
    PLANNING_PROFILE,
    FAST_PROFILE,
    THOROUGH_PROFILE,
    PROFILES,
    get_profile,
    list_profiles,
    register_profile,
    unregister_profile,
)

# Cognitive Engines
from tangku_agentos.cognitive_system.engines.perception import PerceptionEngine
from tangku_agentos.cognitive_system.engines.attention import AttentionEngine
from tangku_agentos.cognitive_system.engines.context import ContextEngine
from tangku_agentos.cognitive_system.engines.reasoning import ReasoningEngine
from tangku_agentos.cognitive_system.engines.planning import PlanningEngine
from tangku_agentos.cognitive_system.engines.reflection import ReflectionEngine
from tangku_agentos.cognitive_system.engines.decision import DecisionEngine
from tangku_agentos.cognitive_system.engines.learning import LearningEngine

# Memory Interfaces
from tangku_agentos.cognitive_system.memory.working_memory import WorkingMemory
from tangku_agentos.cognitive_system.memory.long_term_memory import LongTermMemoryInterface

# Knowledge Interface
from tangku_agentos.cognitive_system.knowledge.knowledge_interface import KnowledgeInterface

# Execution Engines
from tangku_agentos.cognitive_system.execution.skill_selection import SkillSelectionEngine
from tangku_agentos.cognitive_system.execution.tool_selection import ToolSelectionEngine
from tangku_agentos.cognitive_system.execution.action_executor import ActionExecutor

# Evaluation Engines
from tangku_agentos.cognitive_system.evaluation.evaluation_engine import EvaluationEngine
from tangku_agentos.cognitive_system.evaluation.confidence_engine import ConfidenceEngine

# Meta-Cognition
from tangku_agentos.cognitive_system.meta.self_monitoring import SelfMonitoringEngine
from tangku_agentos.cognitive_system.meta.meta_cognition import MetaCognitionEngine

# Goal Management
from tangku_agentos.cognitive_system.goals.goal_manager import GoalManager

# Models
from tangku_agentos.cognitive_system.models.cognitive_input import CognitiveInput
from tangku_agentos.cognitive_system.models.cognitive_output import CognitiveOutput
from tangku_agentos.cognitive_system.models.other_models import (
    MemoryEntry,
    KnowledgeQuery,
    ReasoningResult,
    PlanningResult,
    DecisionResult,
    ActionPlan,
)

# Exceptions
from tangku_agentos.cognitive_system.exceptions import (
    CognitiveError,
    PerceptionError,
    AttentionError,
    ContextError,
    MemoryError,
    KnowledgeError,
    ReasoningError,
    PlanningError,
    DecisionError,
    ExecutionError,
    EvaluationError,
    LearningError,
    ConfidenceError,
    MonitoringError,
    MetaCognitionError,
    AgentError,
)

# Agent Capabilities
from tangku_agentos.cognitive_system.core.cognitive_agent import AgentCapabilities

__all__ = [
    # Cognitive Core
    "CognitiveAgent",
    "CognitiveConfig",
    "MemoryConfig",
    "KnowledgeConfig",
    "ReasoningConfig",
    "PlanningConfig",
    "DecisionConfig",
    "AttentionConfig",
    "LearningConfig",
    "ExecutionConfig",
    "EvaluationConfig",
    "MonitoringConfig",
    "MetaCognitionConfig",
    "ReasoningMode",
    "MemoryStrategy",
    "KnowledgeStrategy",
    "LearningStrategy",
    "DecisionStrategy",
    "PlanningStrategy",
    "AttentionStrategy",
    "create_cognitive_config",
    "CognitiveState",
    "CognitiveStateEnum",
    "CognitiveStage",
    "CognitiveMetrics",
    "CognitiveContext",
    "CognitiveLoop",
    "LoopMode",
    "LoopStatus",
    "LoopMetrics",
    "LoopHooks",
    "CognitiveProfile",
    "ANALYTICAL_PROFILE",
    "CREATIVE_PROFILE",
    "RESEARCH_PROFILE",
    "CODING_PROFILE",
    "PLANNING_PROFILE",
    "FAST_PROFILE",
    "THOROUGH_PROFILE",
    "PROFILES",
    "get_profile",
    "list_profiles",
    "register_profile",
    "unregister_profile",
    # Cognitive Engines
    "PerceptionEngine",
    "AttentionEngine",
    "ContextEngine",
    "ReasoningEngine",
    "PlanningEngine",
    "ReflectionEngine",
    "DecisionEngine",
    "LearningEngine",
    # Memory Interfaces
    "WorkingMemory",
    "LongTermMemoryInterface",
    # Knowledge Interface
    "KnowledgeInterface",
    # Execution Engines
    "SkillSelectionEngine",
    "ToolSelectionEngine",
    "ActionExecutor",
    # Evaluation Engines
    "EvaluationEngine",
    "ConfidenceEngine",
    # Meta-Cognition
    "SelfMonitoringEngine",
    "MetaCognitionEngine",
    # Goal Management
    "GoalManager",
    # Models
    "CognitiveInput",
    "CognitiveOutput",
    "MemoryEntry",
    "KnowledgeQuery",
    "ReasoningResult",
    "PlanningResult",
    "DecisionResult",
    "ActionPlan",
    # Exceptions
    "CognitiveError",
    "PerceptionError",
    "AttentionError",
    "ContextError",
    "MemoryError",
    "KnowledgeError",
    "ReasoningError",
    "PlanningError",
    "DecisionError",
    "ExecutionError",
    "EvaluationError",
    "LearningError",
    "ConfidenceError",
    "MonitoringError",
    "MetaCognitionError",
    "AgentError",
    # Agent Capabilities
    "AgentCapabilities",
]
