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
"""

# Cognitive Core
from tangku_agentos.cognitive_system.core.cognitive_agent import CognitiveAgent, AgentCapabilities
from tangku_agentos.cognitive_system.core.cognitive_config import (
    CognitiveConfig, MemoryConfig, KnowledgeConfig, ReasoningConfig,
    PlanningConfig, DecisionConfig, AttentionConfig, LearningConfig,
    ExecutionConfig, EvaluationConfig, MonitoringConfig, MetaCognitionConfig,
    ReasoningMode, MemoryStrategy, KnowledgeStrategy, LearningStrategy,
    DecisionStrategy, PlanningStrategy, AttentionStrategy, create_cognitive_config
)
from tangku_agentos.cognitive_system.core.cognitive_state import (
    CognitiveState, CognitiveStateEnum, CognitiveStage, CognitiveMetrics, CognitiveContext
)
from tangku_agentos.cognitive_system.core.cognitive_loop import (
    CognitiveLoop, LoopMode, LoopStatus, LoopMetrics, LoopHooks
)
from tangku_agentos.cognitive_system.core.cognitive_profile import (
    CognitiveProfile, ANALYTICAL_PROFILE, CREATIVE_PROFILE, RESEARCH_PROFILE,
    CODING_PROFILE, PLANNING_PROFILE, FAST_PROFILE, THOROUGH_PROFILE,
    PROFILES, get_profile, list_profiles, register_profile, unregister_profile
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
from tangku_agentos.cognitive_system.memory.episodic_memory import EpisodicMemoryInterface
from tangku_agentos.cognitive_system.memory.semantic_memory import SemanticMemoryInterface
from tangku_agentos.cognitive_system.memory.memory_consolidation import MemoryConsolidationEngine

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
    MemoryEntry, KnowledgeQuery, ReasoningResult, PlanningResult,
    DecisionResult, ActionPlan
)

# Exceptions
from tangku_agentos.cognitive_system.exceptions import (
    CognitiveError, PerceptionError, AttentionError, ContextError,
    MemoryError, KnowledgeError, ReasoningError, PlanningError,
    DecisionError, ExecutionError, EvaluationError, LearningError,
    ConfidenceError, MonitoringError, MetaCognitionError, AgentError
)

__all__ = [
    # Cognitive Core
    "CognitiveAgent", "AgentCapabilities",
    "CognitiveConfig", "MemoryConfig", "KnowledgeConfig", "ReasoningConfig",
    "PlanningConfig", "DecisionConfig", "AttentionConfig", "LearningConfig",
    "ExecutionConfig", "EvaluationConfig", "MonitoringConfig", "MetaCognitionConfig",
    "ReasoningMode", "MemoryStrategy", "KnowledgeStrategy", "LearningStrategy",
    "DecisionStrategy", "PlanningStrategy", "AttentionStrategy", "create_cognitive_config",
    "CognitiveState", "CognitiveStateEnum", "CognitiveStage", "CognitiveMetrics", "CognitiveContext",
    "CognitiveLoop", "LoopMode", "LoopStatus", "LoopMetrics", "LoopHooks",
    "CognitiveProfile", "ANALYTICAL_PROFILE", "CREATIVE_PROFILE", "RESEARCH_PROFILE",
    "CODING_PROFILE", "PLANNING_PROFILE", "FAST_PROFILE", "THOROUGH_PROFILE",
    # Cognitive Engines
    "PerceptionEngine", "AttentionEngine", "ContextEngine", "ReasoningEngine",
    "PlanningEngine", "ReflectionEngine", "DecisionEngine", "LearningEngine",
    # Memory Interfaces
    "WorkingMemory", "LongTermMemoryInterface", "EpisodicMemoryInterface",
    "SemanticMemoryInterface", "MemoryConsolidationEngine",
    # Knowledge Interface
    "KnowledgeInterface",
    # Execution Engines
    "SkillSelectionEngine", "ToolSelectionEngine", "ActionExecutor",
    # Evaluation Engines
    "EvaluationEngine", "ConfidenceEngine",
    # Meta-Cognition
    "SelfMonitoringEngine", "MetaCognitionEngine",
    # Goal Management
    "GoalManager",
    # Models
    "CognitiveInput", "CognitiveOutput", "MemoryEntry", "KnowledgeQuery",
    "ReasoningResult", "PlanningResult", "DecisionResult", "ActionPlan",
    # Exceptions
    "CognitiveError", "PerceptionError", "AttentionError", "ContextError",
    "MemoryError", "KnowledgeError", "ReasoningError", "PlanningError",
    "DecisionError", "ExecutionError", "EvaluationError", "LearningError",
    "ConfidenceError", "MonitoringError", "MetaCognitionError", "AgentError"
]
