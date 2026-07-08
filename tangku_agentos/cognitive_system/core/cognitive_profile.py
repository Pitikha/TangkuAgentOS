"""
AI Cognitive System - Cognitive Profiles

This module provides cognitive profiles that define different thinking styles
and approaches for cognitive agents. Each profile configures the agent's
behavior, reasoning style, and cognitive capabilities.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import (
        CognitiveConfig,
        ReasoningMode,
        MemoryStrategy,
        KnowledgeStrategy,
        LearningStrategy,
        DecisionStrategy,
        PlanningStrategy,
        AttentionStrategy,
    )


@dataclass
class CognitiveProfile:
    """
    A cognitive profile defines a thinking style for cognitive agents.
    
    Each profile configures the agent's behavior across multiple dimensions:
    - Reasoning style and depth
    - Memory usage and strategy
    - Knowledge acquisition and usage
    - Planning approach
    - Decision making strategy
    - Attention and focus
    - Learning approach
    
    Attributes:
        name: Name of the profile.
        description: Description of the profile.
        reasoning_mode: Default reasoning mode.
        reasoning_config: Configuration for reasoning.
        memory_strategy: Memory strategy.
        memory_config: Configuration for memory.
        knowledge_strategy: Knowledge strategy.
        knowledge_config: Configuration for knowledge.
        planning_strategy: Planning strategy.
        planning_config: Configuration for planning.
        decision_strategy: Decision strategy.
        decision_config: Configuration for decision making.
        attention_strategy: Attention strategy.
        attention_config: Configuration for attention.
        learning_strategy: Learning strategy.
        learning_config: Configuration for learning.
        execution_config: Configuration for execution.
        evaluation_config: Configuration for evaluation.
        monitoring_config: Configuration for monitoring.
        meta_cognition_config: Configuration for meta-cognition.
        enabled_modules: Set of enabled cognitive modules.
        disabled_modules: Set of disabled cognitive modules.
        resource_requirements: Resource requirements for this profile.
    """

    name: str
    description: str
    reasoning_mode: "ReasoningMode" = "ReasoningMode.GENERAL"
    reasoning_config: Dict[str, Any] = field(default_factory=dict)
    memory_strategy: "MemoryStrategy" = "MemoryStrategy.BALANCED"
    memory_config: Dict[str, Any] = field(default_factory=dict)
    knowledge_strategy: "KnowledgeStrategy" = "KnowledgeStrategy.BALANCED"
    knowledge_config: Dict[str, Any] = field(default_factory=dict)
    planning_strategy: "PlanningStrategy" = "PlanningStrategy.HIERARCHICAL"
    planning_config: Dict[str, Any] = field(default_factory=dict)
    decision_strategy: "DecisionStrategy" = "DecisionStrategy.BALANCED"
    decision_config: Dict[str, Any] = field(default_factory=dict)
    attention_strategy: "AttentionStrategy" = "AttentionStrategy.PRIORITY"
    attention_config: Dict[str, Any] = field(default_factory=dict)
    learning_strategy: "LearningStrategy" = "LearningStrategy.CONTINUAL"
    learning_config: Dict[str, Any] = field(default_factory=dict)
    execution_config: Dict[str, Any] = field(default_factory=dict)
    evaluation_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    meta_cognition_config: Dict[str, Any] = field(default_factory=dict)
    enabled_modules: Set[str] = field(default_factory=set)
    disabled_modules: Set[str] = field(default_factory=set)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

    def to_config(self) -> "CognitiveConfig":
        """
        Convert this profile to a cognitive configuration.
        
        Returns:
            CognitiveConfig instance.
        """
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
        )

        return CognitiveConfig(
            agent_id="",  # Will be set separately
            agent_name=f"Agent ({self.name})",
            agent_description=self.description,
            profile=self.name,
            enabled_modules=self.enabled_modules,
            disabled_modules=self.disabled_modules,
            memory=MemoryConfig(**self.memory_config),
            knowledge=KnowledgeConfig(**self.knowledge_config),
            reasoning=ReasoningConfig(**self.reasoning_config),
            planning=PlanningConfig(**self.planning_config),
            decision=DecisionConfig(**self.decision_config),
            attention=AttentionConfig(**self.attention_config),
            learning=LearningConfig(**self.learning_config),
            execution=ExecutionConfig(**self.execution_config),
            evaluation=EvaluationConfig(**self.evaluation_config),
            monitoring=MonitoringConfig(**self.monitoring_config),
            meta_cognition=MetaCognitionConfig(**self.meta_cognition_config),
            resource_limits=self.resource_requirements,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "reasoning_mode": self.reasoning_mode.value if hasattr(self.reasoning_mode, 'value') else str(self.reasoning_mode),
            "reasoning_config": self.reasoning_config,
            "memory_strategy": self.memory_strategy.value if hasattr(self.memory_strategy, 'value') else str(self.memory_strategy),
            "memory_config": self.memory_config,
            "knowledge_strategy": self.knowledge_strategy.value if hasattr(self.knowledge_strategy, 'value') else str(self.knowledge_strategy),
            "knowledge_config": self.knowledge_config,
            "planning_strategy": self.planning_strategy.value if hasattr(self.planning_strategy, 'value') else str(self.planning_strategy),
            "planning_config": self.planning_config,
            "decision_strategy": self.decision_strategy.value if hasattr(self.decision_strategy, 'value') else str(self.decision_strategy),
            "decision_config": self.decision_config,
            "attention_strategy": self.attention_strategy.value if hasattr(self.attention_strategy, 'value') else str(self.attention_strategy),
            "attention_config": self.attention_config,
            "learning_strategy": self.learning_strategy.value if hasattr(self.learning_strategy, 'value') else str(self.learning_strategy),
            "learning_config": self.learning_config,
            "execution_config": self.execution_config,
            "evaluation_config": self.evaluation_config,
            "monitoring_config": self.monitoring_config,
            "meta_cognition_config": self.meta_cognition_config,
            "enabled_modules": list(self.enabled_modules),
            "disabled_modules": list(self.disabled_modules),
            "resource_requirements": self.resource_requirements,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveProfile":
        """Create profile from dictionary."""
        from tangku_agentos.cognitive_system.core.cognitive_config import (
            ReasoningMode,
            MemoryStrategy,
            KnowledgeStrategy,
            LearningStrategy,
            DecisionStrategy,
            PlanningStrategy,
            AttentionStrategy,
        )

        # Convert string values to enums
        reasoning_mode = ReasoningMode(data.get("reasoning_mode", "GENERAL"))
        memory_strategy = MemoryStrategy(data.get("memory_strategy", "BALANCED"))
        knowledge_strategy = KnowledgeStrategy(data.get("knowledge_strategy", "BALANCED"))
        planning_strategy = PlanningStrategy(data.get("planning_strategy", "HIERARCHICAL"))
        decision_strategy = DecisionStrategy(data.get("decision_strategy", "BALANCED"))
        attention_strategy = AttentionStrategy(data.get("attention_strategy", "PRIORITY"))
        learning_strategy = LearningStrategy(data.get("learning_strategy", "CONTINUAL"))

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            reasoning_mode=reasoning_mode,
            reasoning_config=data.get("reasoning_config", {}),
            memory_strategy=memory_strategy,
            memory_config=data.get("memory_config", {}),
            knowledge_strategy=knowledge_strategy,
            knowledge_config=data.get("knowledge_config", {}),
            planning_strategy=planning_strategy,
            planning_config=data.get("planning_config", {}),
            decision_strategy=decision_strategy,
            decision_config=data.get("decision_config", {}),
            attention_strategy=attention_strategy,
            attention_config=data.get("attention_config", {}),
            learning_strategy=learning_strategy,
            learning_config=data.get("learning_config", {}),
            execution_config=data.get("execution_config", {}),
            evaluation_config=data.get("evaluation_config", {}),
            monitoring_config=data.get("monitoring_config", {}),
            meta_cognition_config=data.get("meta_cognition_config", {}),
            enabled_modules=set(data.get("enabled_modules", [])),
            disabled_modules=set(data.get("disabled_modules", [])),
            resource_requirements=data.get("resource_requirements", {}),
        )


# Pre-defined cognitive profiles

ANALYTICAL_PROFILE = CognitiveProfile(
    name="analytical",
    description="Logical, step-by-step reasoning with deep analysis",
    reasoning_mode="ReasoningMode.ANALYTICAL",
    reasoning_config={
        "max_depth": 15,
        "max_branches": 3,
        "temperature": 0.3,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": False,
        "graph_reasoning_enabled": True,
    },
    memory_strategy="MemoryStrategy.BALANCED",
    memory_config={
        "working_memory_size": 1500,
        "short_term_memory_size": 6000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 172800.0,  # 48 hours
    },
    knowledge_strategy="KnowledgeStrategy.DEEP",
    knowledge_config={
        "search_limit": 80,
        "similarity_threshold": 0.8,
        "confidence_threshold": 0.7,
        "knowledge_fusion_enabled": True,
        "knowledge_verification_enabled": True,
    },
    planning_strategy="PlanningStrategy.HIERARCHICAL",
    planning_config={
        "max_plan_depth": 12,
        "max_plan_branches": 4,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
    },
    decision_strategy="DecisionStrategy.UTILITY",
    decision_config={
        "utility_weights": {"benefit": 0.5, "cost": 0.3, "risk": 0.1, "confidence": 0.1},
        "permission_check_enabled": True,
        "resource_check_enabled": True,
    },
    attention_strategy="AttentionStrategy.FOCUSED",
    attention_config={
        "max_focus_items": 3,
        "focus_switch_threshold": 0.9,
        "priority_weights": {"goal_relevance": 0.5, "urgency": 0.3, "importance": 0.1, "novelty": 0.1},
    },
    learning_strategy="LearningStrategy.PATTERN",
    learning_config={
        "learning_rate": 0.15,
        "pattern_learning_enabled": True,
        "failure_learning_enabled": True,
        "memory_optimization_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 3,
        "action_timeout": 90.0,
        "retry_enabled": True,
        "max_retries": 2,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["accuracy", "completeness", "relevance", "efficiency"],
        "outcome_tracking_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "goal_monitoring_enabled": True,
        "monitoring_interval": 30.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "metacognition_interval": 600.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "medium",
        "memory": "high",
        "storage": "medium",
    },
)

CREATIVE_PROFILE = CognitiveProfile(
    name="creative",
    description="Innovative, outside-the-box thinking with high creativity",
    reasoning_mode="ReasoningMode.CREATIVE",
    reasoning_config={
        "max_depth": 10,
        "max_branches": 8,
        "temperature": 0.9,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": True,
        "graph_reasoning_enabled": True,
    },
    memory_strategy="MemoryStrategy.CONTEXTUAL",
    memory_config={
        "working_memory_size": 2000,
        "short_term_memory_size": 8000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 86400.0,  # 24 hours
    },
    knowledge_strategy="KnowledgeStrategy.BROAD",
    knowledge_config={
        "search_limit": 100,
        "similarity_threshold": 0.6,
        "confidence_threshold": 0.5,
        "knowledge_fusion_enabled": True,
        "knowledge_linking_enabled": True,
    },
    planning_strategy="PlanningStrategy.ADAPTIVE",
    planning_config={
        "max_plan_depth": 8,
        "max_plan_branches": 6,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
    },
    decision_strategy="DecisionStrategy.RISK_SEEKING",
    decision_config={
        "utility_weights": {"benefit": 0.6, "cost": 0.2, "risk": 0.1, "confidence": 0.1},
        "permission_check_enabled": True,
        "resource_check_enabled": False,
    },
    attention_strategy="AttentionStrategy.BROAD",
    attention_config={
        "max_focus_items": 10,
        "focus_switch_threshold": 0.6,
        "priority_weights": {"goal_relevance": 0.3, "urgency": 0.2, "importance": 0.2, "novelty": 0.3},
    },
    learning_strategy="LearningStrategy.CONTINUAL",
    learning_config={
        "learning_rate": 0.2,
        "experience_learning_enabled": True,
        "pattern_learning_enabled": True,
        "preference_learning_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 5,
        "action_timeout": 60.0,
        "retry_enabled": True,
        "max_retries": 3,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["novelty", "originality", "relevance", "impact"],
        "outcome_tracking_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "goal_monitoring_enabled": True,
        "monitoring_interval": 60.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "cognitive_flexibility_enabled": True,
        "metacognition_interval": 300.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "high",
        "memory": "high",
        "storage": "medium",
    },
)

RESEARCH_PROFILE = CognitiveProfile(
    name="research",
    description="Thorough, evidence-based analysis with deep knowledge exploration",
    reasoning_mode="ReasoningMode.RESEARCH",
    reasoning_config={
        "max_depth": 20,
        "max_branches": 5,
        "temperature": 0.4,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": False,
        "graph_reasoning_enabled": True,
    },
    memory_strategy="MemoryStrategy.LONG_TERM",
    memory_config={
        "working_memory_size": 2500,
        "short_term_memory_size": 10000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 604800.0,  # 7 days
    },
    knowledge_strategy="KnowledgeStrategy.DEEP",
    knowledge_config={
        "search_limit": 150,
        "similarity_threshold": 0.85,
        "confidence_threshold": 0.8,
        "knowledge_fusion_enabled": True,
        "knowledge_verification_enabled": True,
        "knowledge_extraction_enabled": True,
    },
    planning_strategy="PlanningStrategy.PROACTIVE",
    planning_config={
        "max_plan_depth": 15,
        "max_plan_branches": 5,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
    },
    decision_strategy="DecisionStrategy.RISK_AVERSE",
    decision_config={
        "utility_weights": {"benefit": 0.4, "cost": 0.3, "risk": 0.2, "confidence": 0.1},
        "permission_check_enabled": True,
        "resource_check_enabled": True,
        "constraint_check_enabled": True,
    },
    attention_strategy="AttentionStrategy.SELECTIVE",
    attention_config={
        "max_focus_items": 5,
        "focus_switch_threshold": 0.85,
        "priority_weights": {"goal_relevance": 0.6, "urgency": 0.2, "importance": 0.15, "novelty": 0.05},
    },
    learning_strategy="LearningStrategy.EPISODIC",
    learning_config={
        "learning_rate": 0.1,
        "episodic_learning_enabled": True,
        "knowledge_refinement_enabled": True,
        "memory_optimization_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 3,
        "action_timeout": 120.0,
        "retry_enabled": True,
        "max_retries": 3,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["accuracy", "completeness", "relevance", "verifiability"],
        "outcome_tracking_enabled": True,
        "expectation_comparison_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "goal_monitoring_enabled": True,
        "monitoring_interval": 45.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "strategy_selection_enabled": True,
        "metacognition_interval": 900.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "high",
        "memory": "very_high",
        "storage": "high",
    },
)

CODING_PROFILE = CognitiveProfile(
    name="coding",
    description="Code-focused reasoning with precise, structured thinking",
    reasoning_mode="ReasoningMode.CODING",
    reasoning_config={
        "max_depth": 12,
        "max_branches": 4,
        "temperature": 0.2,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": False,
        "graph_reasoning_enabled": True,
    },
    memory_strategy="MemoryStrategy.SELECTIVE",
    memory_config={
        "working_memory_size": 3000,
        "short_term_memory_size": 10000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 259200.0,  # 3 days
    },
    knowledge_strategy="KnowledgeStrategy.BALANCED",
    knowledge_config={
        "search_limit": 100,
        "similarity_threshold": 0.75,
        "confidence_threshold": 0.6,
        "knowledge_fusion_enabled": True,
        "knowledge_extraction_enabled": True,
    },
    planning_strategy="PlanningStrategy.HIERARCHICAL",
    planning_config={
        "max_plan_depth": 10,
        "max_plan_branches": 3,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
    },
    decision_strategy="DecisionStrategy.COST_BASED",
    decision_config={
        "utility_weights": {"benefit": 0.3, "cost": 0.4, "risk": 0.2, "confidence": 0.1},
        "cost_weights": {"computation": 0.5, "time": 0.3, "resources": 0.2},
        "permission_check_enabled": True,
        "resource_check_enabled": True,
    },
    attention_strategy="AttentionStrategy.FOCUSED",
    attention_config={
        "max_focus_items": 2,
        "focus_switch_threshold": 0.95,
        "priority_weights": {"goal_relevance": 0.7, "urgency": 0.2, "importance": 0.1, "novelty": 0.0},
    },
    learning_strategy="LearningStrategy.PATTERN",
    learning_config={
        "learning_rate": 0.15,
        "pattern_learning_enabled": True,
        "failure_learning_enabled": True,
        "success_reinforcement_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 2,
        "action_timeout": 180.0,
        "retry_enabled": True,
        "max_retries": 2,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["correctness", "efficiency", "completeness", "maintainability"],
        "outcome_tracking_enabled": True,
        "lesson_generation_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "goal_monitoring_enabled": True,
        "monitoring_interval": 30.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "strategy_adjustment_enabled": True,
        "metacognition_interval": 600.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "medium",
        "memory": "high",
        "storage": "medium",
    },
)

PLANNING_PROFILE = CognitiveProfile(
    name="planning",
    description="Strategic, goal-oriented thinking with comprehensive planning",
    reasoning_mode="ReasoningMode.PLANNING",
    reasoning_config={
        "max_depth": 15,
        "max_branches": 6,
        "temperature": 0.5,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": True,
        "graph_reasoning_enabled": True,
    },
    memory_strategy="MemoryStrategy.CONTEXTUAL",
    memory_config={
        "working_memory_size": 2000,
        "short_term_memory_size": 8000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 345600.0,  # 4 days
    },
    knowledge_strategy="KnowledgeStrategy.BROAD",
    knowledge_config={
        "search_limit": 120,
        "similarity_threshold": 0.7,
        "confidence_threshold": 0.6,
        "knowledge_fusion_enabled": True,
        "knowledge_linking_enabled": True,
    },
    planning_strategy="PlanningStrategy.OPTIMAL",
    planning_config={
        "max_plan_depth": 20,
        "max_plan_branches": 8,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
        "rollback_planning_enabled": True,
        "recovery_planning_enabled": True,
        "parallel_planning_enabled": True,
    },
    decision_strategy="DecisionStrategy.BALANCED",
    decision_config={
        "utility_weights": {"benefit": 0.4, "cost": 0.3, "risk": 0.2, "confidence": 0.1},
        "permission_check_enabled": True,
        "resource_check_enabled": True,
        "constraint_check_enabled": True,
    },
    attention_strategy="AttentionStrategy.GOAL_BASED",
    attention_config={
        "max_focus_items": 4,
        "focus_switch_threshold": 0.8,
        "priority_weights": {"goal_relevance": 0.8, "urgency": 0.1, "importance": 0.05, "novelty": 0.05},
    },
    learning_strategy="LearningStrategy.REINFORCEMENT",
    learning_config={
        "learning_rate": 0.12,
        "success_reinforcement_enabled": True,
        "failure_learning_enabled": True,
        "preference_learning_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 4,
        "action_timeout": 120.0,
        "retry_enabled": True,
        "max_retries": 3,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["effectiveness", "efficiency", "completeness", "adaptability"],
        "outcome_tracking_enabled": True,
        "strategy_update_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "goal_monitoring_enabled": True,
        "strategy_adjustment_enabled": True,
        "monitoring_interval": 60.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "cognitive_flexibility_enabled": True,
        "strategy_selection_enabled": True,
        "metacognition_interval": 300.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "high",
        "memory": "high",
        "storage": "medium",
    },
)

FAST_PROFILE = CognitiveProfile(
    name="fast",
    description="Quick, efficient responses with minimal resource usage",
    reasoning_mode="ReasoningMode.FAST",
    reasoning_config={
        "max_depth": 5,
        "max_branches": 2,
        "temperature": 0.7,
        "chain_of_thought_enabled": False,
        "tree_of_thought_enabled": False,
        "graph_reasoning_enabled": False,
        "reasoning_timeout": 10.0,
        "reasoning_cache_enabled": True,
    },
    memory_strategy="MemoryStrategy.SELECTIVE",
    memory_config={
        "working_memory_size": 500,
        "short_term_memory_size": 2000,
        "memory_consolidation_enabled": False,
        "memory_expiration_age": 3600.0,  # 1 hour
    },
    knowledge_strategy="KnowledgeStrategy.CONTEXTUAL",
    knowledge_config={
        "search_limit": 20,
        "similarity_threshold": 0.8,
        "confidence_threshold": 0.7,
        "knowledge_fusion_enabled": False,
        "knowledge_verification_enabled": False,
    },
    planning_strategy="PlanningStrategy.REACTIVE",
    planning_config={
        "max_plan_depth": 3,
        "max_plan_branches": 2,
        "plan_optimization_enabled": False,
        "adaptive_replanning_enabled": False,
        "planning_timeout": 5.0,
    },
    decision_strategy="DecisionStrategy.FAST",
    decision_config={
        "utility_weights": {"benefit": 0.5, "cost": 0.3, "risk": 0.1, "confidence": 0.1},
        "permission_check_enabled": False,
        "resource_check_enabled": False,
        "decision_timeout": 2.0,
    },
    attention_strategy="AttentionStrategy.PRIORITY",
    attention_config={
        "max_focus_items": 1,
        "focus_switch_threshold": 0.9,
        "priority_weights": {"goal_relevance": 0.5, "urgency": 0.3, "importance": 0.2, "novelty": 0.0},
    },
    learning_strategy="LearningStrategy.FEEDBACK",
    learning_config={
        "learning_rate": 0.05,
        "feedback_integration_enabled": True,
        "memory_optimization_enabled": False,
        "knowledge_refinement_enabled": False,
    },
    execution_config={
        "max_concurrent_actions": 1,
        "action_timeout": 30.0,
        "retry_enabled": False,
        "max_retries": 0,
    },
    evaluation_config={
        "confidence_calculation_enabled": False,
        "evaluation_metrics": ["speed", "responsiveness"],
        "outcome_tracking_enabled": False,
    },
    monitoring_config={
        "self_evaluation_enabled": False,
        "self_correction_enabled": False,
        "goal_monitoring_enabled": False,
        "monitoring_interval": 120.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": False,
        "self_reflection_enabled": False,
        "cognitive_flexibility_enabled": False,
        "metacognition_interval": 3600.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "knowledge", "reasoning", "planning", "decision",
        "tool_selection", "action_executor", "evaluation",
    },
    disabled_modules={
        "long_term_memory", "episodic_memory", "semantic_memory",
        "reflection", "goal_manager", "learning", "skill_selection",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "low",
        "memory": "low",
        "storage": "low",
    },
)

THOROUGH_PROFILE = CognitiveProfile(
    name="thorough",
    description="Comprehensive, detailed analysis with exhaustive exploration",
    reasoning_mode="ReasoningMode.THOROUGH",
    reasoning_config={
        "max_depth": 20,
        "max_branches": 10,
        "temperature": 0.5,
        "chain_of_thought_enabled": True,
        "tree_of_thought_enabled": True,
        "graph_reasoning_enabled": True,
        "max_iterations": 500,
        "reasoning_timeout": 120.0,
    },
    memory_strategy="MemoryStrategy.LONG_TERM",
    memory_config={
        "working_memory_size": 3000,
        "short_term_memory_size": 15000,
        "memory_consolidation_enabled": True,
        "memory_expiration_age": 604800.0,  # 7 days
    },
    knowledge_strategy="KnowledgeStrategy.DEEP",
    knowledge_config={
        "search_limit": 200,
        "similarity_threshold": 0.9,
        "confidence_threshold": 0.85,
        "knowledge_fusion_enabled": True,
        "knowledge_verification_enabled": True,
        "knowledge_extraction_enabled": True,
        "knowledge_linking_enabled": True,
    },
    planning_strategy="PlanningStrategy.SATISFICING",
    planning_config={
        "max_plan_depth": 25,
        "max_plan_branches": 10,
        "plan_optimization_enabled": True,
        "adaptive_replanning_enabled": True,
        "rollback_planning_enabled": True,
        "recovery_planning_enabled": True,
    },
    decision_strategy="DecisionStrategy.RISK_AVERSE",
    decision_config={
        "utility_weights": {"benefit": 0.3, "cost": 0.3, "risk": 0.3, "confidence": 0.1},
        "risk_weights": {"probability": 0.7, "impact": 0.3},
        "permission_check_enabled": True,
        "resource_check_enabled": True,
        "constraint_check_enabled": True,
    },
    attention_strategy="AttentionStrategy.SELECTIVE",
    attention_config={
        "max_focus_items": 8,
        "focus_switch_threshold": 0.7,
        "priority_weights": {"goal_relevance": 0.5, "urgency": 0.2, "importance": 0.2, "novelty": 0.1},
    },
    learning_strategy="LearningStrategy.CONTINUAL",
    learning_config={
        "learning_rate": 0.1,
        "memory_learning_enabled": True,
        "experience_learning_enabled": True,
        "pattern_learning_enabled": True,
        "failure_learning_enabled": True,
        "success_reinforcement_enabled": True,
        "feedback_integration_enabled": True,
        "preference_learning_enabled": True,
        "memory_optimization_enabled": True,
        "knowledge_refinement_enabled": True,
    },
    execution_config={
        "max_concurrent_actions": 3,
        "action_timeout": 180.0,
        "retry_enabled": True,
        "max_retries": 5,
    },
    evaluation_config={
        "confidence_calculation_enabled": True,
        "evaluation_metrics": ["accuracy", "completeness", "relevance", "efficiency", "verifiability"],
        "outcome_tracking_enabled": True,
        "expectation_comparison_enabled": True,
        "lesson_generation_enabled": True,
        "strategy_update_enabled": True,
    },
    monitoring_config={
        "self_evaluation_enabled": True,
        "self_correction_enabled": True,
        "self_awareness_enabled": True,
        "goal_monitoring_enabled": True,
        "strategy_adjustment_enabled": True,
        "reflection_scheduling_enabled": True,
        "performance_optimization_enabled": True,
        "monitoring_interval": 30.0,
    },
    meta_cognition_config={
        "higher_order_thinking_enabled": True,
        "self_reflection_enabled": True,
        "cognitive_flexibility_enabled": True,
        "metacognitive_knowledge_enabled": True,
        "strategy_selection_enabled": True,
        "monitoring_accuracy_enabled": True,
        "metacognition_interval": 300.0,
    },
    enabled_modules={
        "perception", "attention", "context", "working_memory",
        "long_term_memory", "episodic_memory", "semantic_memory",
        "knowledge", "reasoning", "planning", "reflection",
        "decision", "goal_manager", "learning", "skill_selection",
        "tool_selection", "action_executor", "evaluation",
        "confidence", "self_monitoring", "meta_cognition",
    },
    resource_requirements={
        "cpu": "very_high",
        "memory": "very_high",
        "storage": "high",
    },
)

# Profile registry
PROFILES: Dict[str, CognitiveProfile] = {
    "analytical": ANALYTICAL_PROFILE,
    "creative": CREATIVE_PROFILE,
    "research": RESEARCH_PROFILE,
    "coding": CODING_PROFILE,
    "planning": PLANNING_PROFILE,
    "fast": FAST_PROFILE,
    "thorough": THOROUGH_PROFILE,
}


def get_profile(name: str) -> Optional[CognitiveProfile]:
    """
    Get a cognitive profile by name.
    
    Args:
        name: Name of the profile.
    
    Returns:
        CognitiveProfile if found, None otherwise.
    """
    return PROFILES.get(name.lower())


def list_profiles() -> List[str]:
    """
    List all available cognitive profiles.
    
    Returns:
        List of profile names.
    """
    return list(PROFILES.keys())


def register_profile(profile: CognitiveProfile) -> None:
    """
    Register a new cognitive profile.
    
    Args:
        profile: Cognitive profile to register.
    """
    PROFILES[profile.name.lower()] = profile


def unregister_profile(name: str) -> bool:
    """
    Unregister a cognitive profile.
    
    Args:
        name: Name of the profile to unregister.
    
    Returns:
        True if profile was found and removed, False otherwise.
    """
    if name.lower() in PROFILES:
        del PROFILES[name.lower()]
        return True
    return False
