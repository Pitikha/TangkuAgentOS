"""
AI Cognitive System - Cognitive Configuration

This module provides configuration classes for the AI Cognitive System.
Each agent can have its own configuration that determines its behavior,
capabilities, and cognitive profile.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class ReasoningMode(Enum):
    """
    Reasoning modes for cognitive agents.
    
    Each mode represents a different approach to reasoning and problem-solving.
    """
    ANALYTICAL = "analytical"          # Logical, step-by-step reasoning
    CREATIVE = "creative"              # Innovative, outside-the-box thinking
    RESEARCH = "research"              # Thorough, evidence-based analysis
    CODING = "coding"                  # Code-focused reasoning
    PLANNING = "planning"              # Strategic, goal-oriented thinking
    SCIENTIFIC = "scientific"          # Hypothesis-driven, experimental
    EDUCATIONAL = "educational"        # Teaching-focused, explanatory
    BUSINESS = "business"              # Practical, results-oriented
    GENERAL = "general"                # Balanced, adaptable reasoning
    FAST = "fast"                      # Quick, efficient responses
    THOROUGH = "thorough"              # Comprehensive, detailed analysis


class MemoryStrategy(Enum):
    """
    Memory strategies for cognitive agents.
    """
    SHORT_TERM = "short_term"          # Focus on working memory
    LONG_TERM = "long_term"            # Prioritize long-term memory
    BALANCED = "balanced"              # Equal focus on all memory types
    CONTEXTUAL = "contextual"          # Memory based on current context
    SELECTIVE = "selective"            # Only most relevant memories


class KnowledgeStrategy(Enum):
    """
    Knowledge strategies for cognitive agents.
    """
    BROAD = "broad"                    # Wide knowledge base
    DEEP = "deep"                      # Specialized knowledge
    BALANCED = "balanced"              # Mix of broad and deep
    CONTEXTUAL = "contextual"          # Knowledge based on context
    RECENT = "recent"                  # Prioritize recent knowledge


class LearningStrategy(Enum):
    """
    Learning strategies for cognitive agents.
    """
    CONTINUAL = "continual"            # Continuous learning from all experiences
    EPISODIC = "episodic"              # Learn from specific events
    PATTERN = "pattern"                # Identify and learn patterns
    FEEDBACK = "feedback"              # Learn from explicit feedback
    REINFORCEMENT = "reinforcement"    # Reinforcement learning
    SUPERVISED = "supervised"          # Supervised learning
    UNSUPERVISED = "unsupervised"      # Unsupervised learning


class DecisionStrategy(Enum):
    """
    Decision strategies for cognitive agents.
    """
    UTILITY = "utility"                # Maximize utility
    RISK_AVERSE = "risk_averse"        # Minimize risk
    RISK_NEUTRAL = "risk_neutral"      # Balanced risk approach
    RISK_SEEKING = "risk_seeking"      # Willing to take risks
    COST_BASED = "cost_based"          # Minimize cost
    TIME_BASED = "time_based"          # Minimize time
    CONFIDENCE = "confidence"          # Maximize confidence
    BALANCED = "balanced"              # Balanced approach


class PlanningStrategy(Enum):
    """
    Planning strategies for cognitive agents.
    """
    HIERARCHICAL = "hierarchical"      # Top-down decomposition
    FLAT = "flat"                      # Single-level planning
    ADAPTIVE = "adaptive"              # Adjust plans as needed
    REACTIVE = "reactive"              # Respond to immediate needs
    PROACTIVE = "proactive"            # Anticipate future needs
    OPTIMAL = "optimal"                # Find optimal plans
    SATISFICING = "satisficing"        # Find good enough plans


class AttentionStrategy(Enum):
    """
    Attention strategies for cognitive agents.
    """
    FOCUSED = "focused"                # Deep focus on current task
    BROAD = "broad"                    # Monitor multiple things
    SELECTIVE = "selective"            # Filter based on relevance
    DYNAMIC = "dynamic"                # Adjust attention dynamically
    PRIORITY = "priority"              # Based on priority scores
    GOAL_BASED = "goal_based"          # Based on goal relevance


@dataclass
class MemoryConfig:
    """
    Configuration for memory management.
    
    Attributes:
        enabled: Whether memory is enabled.
        strategy: Memory strategy to use.
        working_memory_size: Maximum size of working memory.
        short_term_memory_size: Maximum size of short-term memory.
        long_term_memory_enabled: Whether long-term memory is enabled.
        episodic_memory_enabled: Whether episodic memory is enabled.
        semantic_memory_enabled: Whether semantic memory is enabled.
        memory_consolidation_enabled: Whether memory consolidation is enabled.
        memory_consolidation_interval: Interval for memory consolidation.
        memory_expiration_enabled: Whether memory expiration is enabled.
        memory_expiration_age: Age at which memories expire.
        memory_compression_enabled: Whether memory compression is enabled.
        memory_ranking_enabled: Whether memory ranking is enabled.
        memory_retrieval_limit: Maximum number of memories to retrieve.
    """
    enabled: bool = True
    strategy: MemoryStrategy = MemoryStrategy.BALANCED
    working_memory_size: int = 1000
    short_term_memory_size: int = 5000
    long_term_memory_enabled: bool = True
    episodic_memory_enabled: bool = True
    semantic_memory_enabled: bool = True
    memory_consolidation_enabled: bool = True
    memory_consolidation_interval: float = 3600.0  # 1 hour
    memory_expiration_enabled: bool = True
    memory_expiration_age: float = 86400.0  # 24 hours
    memory_compression_enabled: bool = True
    memory_ranking_enabled: bool = True
    memory_retrieval_limit: int = 100


@dataclass
class KnowledgeConfig:
    """
    Configuration for knowledge management.
    
    Attributes:
        enabled: Whether knowledge is enabled.
        strategy: Knowledge strategy to use.
        search_limit: Maximum number of knowledge items to search.
        similarity_threshold: Threshold for similarity matching.
        confidence_threshold: Minimum confidence for knowledge.
        knowledge_fusion_enabled: Whether to fuse multiple knowledge sources.
        knowledge_verification_enabled: Whether to verify knowledge.
        knowledge_extraction_enabled: Whether to extract knowledge from inputs.
        knowledge_linking_enabled: Whether to link related knowledge.
        knowledge_updates_enabled: Whether to update knowledge.
    """
    enabled: bool = True
    strategy: KnowledgeStrategy = KnowledgeStrategy.BALANCED
    search_limit: int = 50
    similarity_threshold: float = 0.7
    confidence_threshold: float = 0.5
    knowledge_fusion_enabled: bool = True
    knowledge_verification_enabled: bool = True
    knowledge_extraction_enabled: bool = True
    knowledge_linking_enabled: bool = True
    knowledge_updates_enabled: bool = True


@dataclass
class ReasoningConfig:
    """
    Configuration for reasoning engine.
    
    Attributes:
        mode: Default reasoning mode.
        max_depth: Maximum reasoning depth.
        max_branches: Maximum number of reasoning branches.
        max_iterations: Maximum number of reasoning iterations.
        temperature: Creativity temperature (0-1).
        top_k: Number of top options to consider.
        top_p: Probability threshold for sampling.
        chain_of_thought_enabled: Whether to use chain of thought.
        tree_of_thought_enabled: Whether to use tree of thought.
        graph_reasoning_enabled: Whether to use graph reasoning.
        multi_agent_reasoning_enabled: Whether to use multi-agent reasoning.
        reasoning_timeout: Timeout for reasoning operations.
        reasoning_cache_enabled: Whether to cache reasoning results.
    """
    mode: ReasoningMode = ReasoningMode.GENERAL
    max_depth: int = 10
    max_branches: int = 5
    max_iterations: int = 100
    temperature: float = 0.7
    top_k: int = 5
    top_p: float = 0.9
    chain_of_thought_enabled: bool = True
    tree_of_thought_enabled: bool = False
    graph_reasoning_enabled: bool = True
    multi_agent_reasoning_enabled: bool = False
    reasoning_timeout: float = 30.0
    reasoning_cache_enabled: bool = True


@dataclass
class PlanningConfig:
    """
    Configuration for planning engine.
    
    Attributes:
        strategy: Planning strategy to use.
        max_plan_depth: Maximum depth of plans.
        max_plan_branches: Maximum number of plan branches.
        max_plan_length: Maximum length of plans.
        plan_optimization_enabled: Whether to optimize plans.
        adaptive_replanning_enabled: Whether to adapt plans dynamically.
        rollback_planning_enabled: Whether to create rollback plans.
        recovery_planning_enabled: Whether to create recovery plans.
        parallel_planning_enabled: Whether to support parallel plans.
        planning_timeout: Timeout for planning operations.
    """
    strategy: PlanningStrategy = PlanningStrategy.HIERARCHICAL
    max_plan_depth: int = 10
    max_plan_branches: int = 5
    max_plan_length: int = 20
    plan_optimization_enabled: bool = True
    adaptive_replanning_enabled: bool = True
    rollback_planning_enabled: bool = True
    recovery_planning_enabled: bool = True
    parallel_planning_enabled: bool = True
    planning_timeout: float = 30.0


@dataclass
class DecisionConfig:
    """
    Configuration for decision engine.
    
    Attributes:
        strategy: Decision strategy to use.
        utility_weights: Weights for utility calculation.
        risk_weights: Weights for risk calculation.
        confidence_weights: Weights for confidence calculation.
        cost_weights: Weights for cost calculation.
        time_weights: Weights for time calculation.
        permission_check_enabled: Whether to check permissions.
        resource_check_enabled: Whether to check resource availability.
        constraint_check_enabled: Whether to check constraints.
        decision_timeout: Timeout for decision making.
    """
    strategy: DecisionStrategy = DecisionStrategy.BALANCED
    utility_weights: Dict[str, float] = field(default_factory=lambda: {
        "benefit": 0.4,
        "cost": 0.3,
        "risk": 0.2,
        "confidence": 0.1,
    })
    risk_weights: Dict[str, float] = field(default_factory=lambda: {
        "probability": 0.6,
        "impact": 0.4,
    })
    confidence_weights: Dict[str, float] = field(default_factory=lambda: {
        "reasoning": 0.4,
        "knowledge": 0.3,
        "memory": 0.2,
        "tool": 0.1,
    })
    cost_weights: Dict[str, float] = field(default_factory=lambda: {
        "computation": 0.4,
        "time": 0.3,
        "resources": 0.3,
    })
    time_weights: Dict[str, float] = field(default_factory=lambda: {
        "urgency": 0.5,
        "duration": 0.5,
    })
    permission_check_enabled: bool = True
    resource_check_enabled: bool = True
    constraint_check_enabled: bool = True
    decision_timeout: float = 10.0


@dataclass
class AttentionConfig:
    """
    Configuration for attention engine.
    
    Attributes:
        strategy: Attention strategy to use.
        priority_weights: Weights for priority calculation.
        novelty_weights: Weights for novelty detection.
        urgency_weights: Weights for urgency calculation.
        importance_weights: Weights for importance calculation.
        max_focus_items: Maximum number of items to focus on.
        focus_switch_threshold: Threshold for switching focus.
        interrupt_handling_enabled: Whether to handle interruptions.
        context_weighting_enabled: Whether to weight by context.
    """
    strategy: AttentionStrategy = AttentionStrategy.PRIORITY
    priority_weights: Dict[str, float] = field(default_factory=lambda: {
        "goal_relevance": 0.4,
        "urgency": 0.3,
        "importance": 0.2,
        "novelty": 0.1,
    })
    novelty_weights: Dict[str, float] = field(default_factory=lambda: {
        "uniqueness": 0.6,
        "surprise": 0.4,
    })
    urgency_weights: Dict[str, float] = field(default_factory=lambda: {
        "time_sensitivity": 0.7,
        "deadline": 0.3,
    })
    importance_weights: Dict[str, float] = field(default_factory=lambda: {
        "impact": 0.6,
        "value": 0.4,
    })
    max_focus_items: int = 5
    focus_switch_threshold: float = 0.8
    interrupt_handling_enabled: bool = True
    context_weighting_enabled: bool = True


@dataclass
class LearningConfig:
    """
    Configuration for learning engine.
    
    Attributes:
        strategy: Learning strategy to use.
        learning_rate: Rate at which to learn.
        memory_learning_enabled: Whether to learn from memory.
        experience_learning_enabled: Whether to learn from experiences.
        pattern_learning_enabled: Whether to learn patterns.
        failure_learning_enabled: Whether to learn from failures.
        success_reinforcement_enabled: Whether to reinforce successes.
        feedback_integration_enabled: Whether to integrate feedback.
        preference_learning_enabled: Whether to learn preferences.
        memory_optimization_enabled: Whether to optimize memory.
        knowledge_refinement_enabled: Whether to refine knowledge.
        learning_interval: Interval for learning operations.
    """
    strategy: LearningStrategy = LearningStrategy.CONTINUAL
    learning_rate: float = 0.1
    memory_learning_enabled: bool = True
    experience_learning_enabled: bool = True
    pattern_learning_enabled: bool = True
    failure_learning_enabled: bool = True
    success_reinforcement_enabled: bool = True
    feedback_integration_enabled: bool = True
    preference_learning_enabled: bool = True
    memory_optimization_enabled: bool = True
    knowledge_refinement_enabled: bool = True
    learning_interval: float = 300.0  # 5 minutes


@dataclass
class ExecutionConfig:
    """
    Configuration for execution engines.
    
    Attributes:
        max_concurrent_actions: Maximum number of concurrent actions.
        action_timeout: Timeout for individual actions.
        retry_enabled: Whether to retry failed actions.
        max_retries: Maximum number of retry attempts.
        retry_backoff: Base backoff time for retries.
        tool_selection_enabled: Whether tool selection is enabled.
        skill_selection_enabled: Whether skill selection is enabled.
        action_validation_enabled: Whether to validate actions.
        action_logging_enabled: Whether to log actions.
        action_metrics_enabled: Whether to collect action metrics.
    """
    max_concurrent_actions: int = 5
    action_timeout: float = 60.0
    retry_enabled: bool = True
    max_retries: int = 3
    retry_backoff: float = 1.0
    tool_selection_enabled: bool = True
    skill_selection_enabled: bool = True
    action_validation_enabled: bool = True
    action_logging_enabled: bool = True
    action_metrics_enabled: bool = True


@dataclass
class EvaluationConfig:
    """
    Configuration for evaluation engines.
    
    Attributes:
        confidence_calculation_enabled: Whether to calculate confidence.
        confidence_thresholds: Thresholds for confidence levels.
        evaluation_metrics: Metrics to track for evaluation.
        outcome_tracking_enabled: Whether to track outcomes.
        expectation_comparison_enabled: Whether to compare with expectations.
        lesson_generation_enabled: Whether to generate lessons.
        strategy_update_enabled: Whether to update strategies.
    """
    confidence_calculation_enabled: bool = True
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9,
    })
    evaluation_metrics: List[str] = field(default_factory=lambda: [
        "accuracy",
        "completeness",
        "relevance",
        "efficiency",
        "satisfaction",
    ])
    outcome_tracking_enabled: bool = True
    expectation_comparison_enabled: bool = True
    lesson_generation_enabled: bool = True
    strategy_update_enabled: bool = True


@dataclass
class MonitoringConfig:
    """
    Configuration for monitoring engines.
    
    Attributes:
        self_evaluation_enabled: Whether self-evaluation is enabled.
        self_correction_enabled: Whether self-correction is enabled.
        self_awareness_enabled: Whether self-awareness is enabled.
        goal_monitoring_enabled: Whether to monitor goals.
        strategy_adjustment_enabled: Whether to adjust strategies.
        reflection_scheduling_enabled: Whether to schedule reflections.
        performance_optimization_enabled: Whether to optimize performance.
        monitoring_interval: Interval for monitoring operations.
    """
    self_evaluation_enabled: bool = True
    self_correction_enabled: bool = True
    self_awareness_enabled: bool = True
    goal_monitoring_enabled: bool = True
    strategy_adjustment_enabled: bool = True
    reflection_scheduling_enabled: bool = True
    performance_optimization_enabled: bool = True
    monitoring_interval: float = 60.0  # 1 minute


@dataclass
class MetaCognitionConfig:
    """
    Configuration for meta-cognition engine.
    
    Attributes:
        higher_order_thinking_enabled: Whether higher-order thinking is enabled.
        self_reflection_enabled: Whether self-reflection is enabled.
        cognitive_flexibility_enabled: Whether cognitive flexibility is enabled.
        metacognitive_knowledge_enabled: Whether metacognitive knowledge is enabled.
        strategy_selection_enabled: Whether strategy selection is enabled.
        monitoring_accuracy_enabled: Whether to monitor accuracy.
        metacognition_interval: Interval for metacognition operations.
    """
    higher_order_thinking_enabled: bool = True
    self_reflection_enabled: bool = True
    cognitive_flexibility_enabled: bool = True
    metacognitive_knowledge_enabled: bool = True
    strategy_selection_enabled: bool = True
    monitoring_accuracy_enabled: bool = True
    metacognition_interval: float = 300.0  # 5 minutes


@dataclass
class CognitiveConfig:
    """
    Main configuration for a cognitive agent.
    
    This class consolidates all configuration options for the AI Cognitive System.
    Each agent can have its own configuration that determines its behavior and
    capabilities.
    
    Attributes:
        agent_id: Unique identifier for the agent.
        agent_name: Human-readable name for the agent.
        agent_description: Description of the agent.
        agent_version: Version of the agent.
        
        # Core Configuration
        profile: Cognitive profile (thinking style).
        enabled_modules: Set of enabled cognitive modules.
        disabled_modules: Set of disabled cognitive modules.
        
        # Module Configurations
        memory: Memory configuration.
        knowledge: Knowledge configuration.
        reasoning: Reasoning configuration.
        planning: Planning configuration.
        decision: Decision configuration.
        attention: Attention configuration.
        learning: Learning configuration.
        execution: Execution configuration.
        evaluation: Evaluation configuration.
        monitoring: Monitoring configuration.
        meta_cognition: Meta-cognition configuration.
        
        # Integration Configuration
        memory_engine_enabled: Whether to integrate with Memory Engine.
        knowledge_engine_enabled: Whether to integrate with Knowledge Engine.
        runtime_communication_enabled: Whether to use Runtime Communication Framework.
        
        # Performance Configuration
        max_iterations: Maximum number of cognitive iterations.
        max_execution_time: Maximum execution time for cognitive operations.
        resource_limits: Resource limits for the agent.
        
        # Debug Configuration
        debug_enabled: Whether debug mode is enabled.
        logging_enabled: Whether logging is enabled.
        metrics_enabled: Whether metrics collection is enabled.
        tracing_enabled: Whether distributed tracing is enabled.
    """
    # Agent Identification
    agent_id: str = ""
    agent_name: str = "Cognitive Agent"
    agent_description: str = "An intelligent agent with cognitive capabilities"
    agent_version: str = "1.0.0"
    
    # Core Configuration
    profile: Optional[str] = None
    enabled_modules: Set[str] = field(default_factory=set)
    disabled_modules: Set[str] = field(default_factory=set)
    
    # Module Configurations
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    planning: PlanningConfig = field(default_factory=PlanningConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    attention: AttentionConfig = field(default_factory=AttentionConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    meta_cognition: MetaCognitionConfig = field(default_factory=MetaCognitionConfig)
    
    # Integration Configuration
    memory_engine_enabled: bool = True
    knowledge_engine_enabled: bool = True
    runtime_communication_enabled: bool = True
    
    # Performance Configuration
    max_iterations: int = 1000
    max_execution_time: float = 300.0  # 5 minutes
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    # Debug Configuration
    debug_enabled: bool = False
    logging_enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Set default enabled modules if not specified
        if not self.enabled_modules:
            self.enabled_modules = {
                "perception",
                "attention",
                "context",
                "working_memory",
                "long_term_memory",
                "episodic_memory",
                "semantic_memory",
                "knowledge",
                "reasoning",
                "planning",
                "reflection",
                "decision",
                "goal_manager",
                "learning",
                "skill_selection",
                "tool_selection",
                "action_executor",
                "evaluation",
                "confidence",
                "self_monitoring",
                "meta_cognition",
            }
        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate the configuration."""
        if not self.agent_id:
            raise ValueError("agent_id is required")
        
        # Validate reasoning mode
        if self.reasoning.mode not in ReasoningMode:
            raise ValueError(f"Invalid reasoning mode: {self.reasoning.mode}")
        
        # Validate memory strategy
        if self.memory.strategy not in MemoryStrategy:
            raise ValueError(f"Invalid memory strategy: {self.memory.strategy}")
        
        # Validate knowledge strategy
        if self.knowledge.strategy not in KnowledgeStrategy:
            raise ValueError(f"Invalid knowledge strategy: {self.knowledge.strategy}")
        
        # Validate learning strategy
        if self.learning.strategy not in LearningStrategy:
            raise ValueError(f"Invalid learning strategy: {self.learning.strategy}")
        
        # Validate decision strategy
        if self.decision.strategy not in DecisionStrategy:
            raise ValueError(f"Invalid decision strategy: {self.decision.strategy}")
        
        # Validate planning strategy
        if self.planning.strategy not in PlanningStrategy:
            raise ValueError(f"Invalid planning strategy: {self.planning.strategy}")
        
        # Validate attention strategy
        if self.attention.strategy not in AttentionStrategy:
            raise ValueError(f"Invalid attention strategy: {self.attention.strategy}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_description": self.agent_description,
            "agent_version": self.agent_version,
            "profile": self.profile,
            "enabled_modules": list(self.enabled_modules),
            "disabled_modules": list(self.disabled_modules),
            "memory": self.memory.to_dict() if hasattr(self.memory, 'to_dict') else str(self.memory),
            "knowledge": self.knowledge.to_dict() if hasattr(self.knowledge, 'to_dict') else str(self.knowledge),
            "reasoning": self.reasoning.to_dict() if hasattr(self.reasoning, 'to_dict') else str(self.reasoning),
            "planning": self.planning.to_dict() if hasattr(self.planning, 'to_dict') else str(self.planning),
            "decision": self.decision.to_dict() if hasattr(self.decision, 'to_dict') else str(self.decision),
            "attention": self.attention.to_dict() if hasattr(self.attention, 'to_dict') else str(self.attention),
            "learning": self.learning.to_dict() if hasattr(self.learning, 'to_dict') else str(self.learning),
            "execution": self.execution.to_dict() if hasattr(self.execution, 'to_dict') else str(self.execution),
            "evaluation": self.evaluation.to_dict() if hasattr(self.evaluation, 'to_dict') else str(self.evaluation),
            "monitoring": self.monitoring.to_dict() if hasattr(self.monitoring, 'to_dict') else str(self.monitoring),
            "meta_cognition": self.meta_cognition.to_dict() if hasattr(self.meta_cognition, 'to_dict') else str(self.meta_cognition),
            "memory_engine_enabled": self.memory_engine_enabled,
            "knowledge_engine_enabled": self.knowledge_engine_enabled,
            "runtime_communication_enabled": self.runtime_communication_enabled,
            "max_iterations": self.max_iterations,
            "max_execution_time": self.max_execution_time,
            "resource_limits": self.resource_limits,
            "debug_enabled": self.debug_enabled,
            "logging_enabled": self.logging_enabled,
            "metrics_enabled": self.metrics_enabled,
            "tracing_enabled": self.tracing_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveConfig":
        """Create configuration from dictionary."""
        # Handle nested configurations
        config_data = data.copy()
        
        if "memory" in config_data and isinstance(config_data["memory"], dict):
            config_data["memory"] = MemoryConfig(**config_data["memory"])
        if "knowledge" in config_data and isinstance(config_data["knowledge"], dict):
            config_data["knowledge"] = KnowledgeConfig(**config_data["knowledge"])
        if "reasoning" in config_data and isinstance(config_data["reasoning"], dict):
            config_data["reasoning"] = ReasoningConfig(**config_data["reasoning"])
        if "planning" in config_data and isinstance(config_data["planning"], dict):
            config_data["planning"] = PlanningConfig(**config_data["planning"])
        if "decision" in config_data and isinstance(config_data["decision"], dict):
            config_data["decision"] = DecisionConfig(**config_data["decision"])
        if "attention" in config_data and isinstance(config_data["attention"], dict):
            config_data["attention"] = AttentionConfig(**config_data["attention"])
        if "learning" in config_data and isinstance(config_data["learning"], dict):
            config_data["learning"] = LearningConfig(**config_data["learning"])
        if "execution" in config_data and isinstance(config_data["execution"], dict):
            config_data["execution"] = ExecutionConfig(**config_data["execution"])
        if "evaluation" in config_data and isinstance(config_data["evaluation"], dict):
            config_data["evaluation"] = EvaluationConfig(**config_data["evaluation"])
        if "monitoring" in config_data and isinstance(config_data["monitoring"], dict):
            config_data["monitoring"] = MonitoringConfig(**config_data["monitoring"])
        if "meta_cognition" in config_data and isinstance(config_data["meta_cognition"], dict):
            config_data["meta_cognition"] = MetaCognitionConfig(**config_data["meta_cognition"])
        
        # Convert sets
        if "enabled_modules" in config_data and isinstance(config_data["enabled_modules"], list):
            config_data["enabled_modules"] = set(config_data["enabled_modules"])
        if "disabled_modules" in config_data and isinstance(config_data["disabled_modules"], list):
            config_data["disabled_modules"] = set(config_data["disabled_modules"])
        
        return cls(**config_data)


def create_cognitive_config(
    agent_id: str = "",
    agent_name: str = "Cognitive Agent",
    profile: str = "general",
    **kwargs,
) -> CognitiveConfig:
    """
    Create a cognitive configuration with sensible defaults.
    
    Args:
        agent_id: Unique identifier for the agent.
        agent_name: Human-readable name for the agent.
        profile: Cognitive profile (thinking style).
        **kwargs: Additional configuration options.
    
    Returns:
        CognitiveConfig instance.
    """
    # Set profile-based defaults
    config_data = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "profile": profile,
    }
    
    # Apply profile-specific settings
    if profile == "analytical":
        config_data["reasoning"] = {
            "mode": ReasoningMode.ANALYTICAL,
            "max_depth": 15,
            "temperature": 0.3,
        }
        config_data["attention"] = {
            "strategy": AttentionStrategy.FOCUSED,
            "max_focus_items": 3,
        }
    elif profile == "creative":
        config_data["reasoning"] = {
            "mode": ReasoningMode.CREATIVE,
            "max_depth": 10,
            "temperature": 0.9,
            "tree_of_thought_enabled": True,
        }
        config_data["attention"] = {
            "strategy": AttentionStrategy.BROAD,
            "max_focus_items": 10,
        }
    elif profile == "research":
        config_data["reasoning"] = {
            "mode": ReasoningMode.RESEARCH,
            "max_depth": 20,
            "max_iterations": 200,
        }
        config_data["knowledge"] = {
            "strategy": KnowledgeStrategy.DEEP,
            "search_limit": 100,
        }
    elif profile == "coding":
        config_data["reasoning"] = {
            "mode": ReasoningMode.CODING,
            "max_depth": 10,
            "temperature": 0.2,
        }
        config_data["memory"] = {
            "working_memory_size": 2000,
        }
    elif profile == "planning":
        config_data["reasoning"] = {
            "mode": ReasoningMode.PLANNING,
            "max_depth": 15,
        }
        config_data["planning"] = {
            "strategy": PlanningStrategy.HIERARCHICAL,
            "max_plan_depth": 15,
        }
    elif profile == "fast":
        config_data["reasoning"] = {
            "mode": ReasoningMode.FAST,
            "max_depth": 5,
            "max_iterations": 50,
            "reasoning_timeout": 10.0,
        }
    elif profile == "thorough":
        config_data["reasoning"] = {
            "mode": ReasoningMode.THOROUGH,
            "max_depth": 20,
            "max_iterations": 500,
            "max_branches": 10,
        }
    
    # Apply user overrides
    config_data.update(kwargs)
    
    return CognitiveConfig(**config_data)
