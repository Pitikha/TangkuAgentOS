"""
AI Cognitive System - Cognitive Agent

This module provides the main CognitiveAgent class, which is the primary
interface for interacting with the AI Cognitive System.

The CognitiveAgent integrates all cognitive modules and provides
a unified interface for processing inputs and generating outputs.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
    from tangku_agentos.cognitive_system.core.cognitive_loop import CognitiveLoop
    from tangku_agentos.cognitive_system.core.cognitive_profile import CognitiveProfile
    from tangku_agentos.cognitive_system.models.cognitive_input import CognitiveInput
    from tangku_agentos.cognitive_system.models.cognitive_output import CognitiveOutput
    from tangku_agentos.cognitive_system.engines.perception import PerceptionEngine
    from tangku_agentos.cognitive_system.engines.attention import AttentionEngine
    from tangku_agentos.cognitive_system.engines.context import ContextEngine
    from tangku_agentos.cognitive_system.engines.reasoning import ReasoningEngine
    from tangku_agentos.cognitive_system.engines.planning import PlanningEngine
    from tangku_agentos.cognitive_system.engines.reflection import ReflectionEngine
    from tangku_agentos.cognitive_system.engines.decision import DecisionEngine
    from tangku_agentos.cognitive_system.engines.learning import LearningEngine
    from tangku_agentos.cognitive_system.memory.working_memory import WorkingMemory
    from tangku_agentos.cognitive_system.memory.long_term_memory import LongTermMemoryInterface
    from tangku_agentos.cognitive_system.knowledge.knowledge_interface import KnowledgeInterface
    from tangku_agentos.cognitive_system.execution.skill_selection import SkillSelectionEngine
    from tangku_agentos.cognitive_system.execution.tool_selection import ToolSelectionEngine
    from tangku_agentos.cognitive_system.execution.action_executor import ActionExecutor
    from tangku_agentos.cognitive_system.evaluation.evaluation_engine import EvaluationEngine
    from tangku_agentos.cognitive_system.evaluation.confidence_engine import ConfidenceEngine
    from tangku_agentos.cognitive_system.meta.self_monitoring import SelfMonitoringEngine
    from tangku_agentos.cognitive_system.meta.meta_cognition import MetaCognitionEngine
    from tangku_agentos.cognitive_system.goals.goal_manager import GoalManager

logger = logging.getLogger(__name__)


@dataclass
class AgentCapabilities:
    """
    Capabilities of a cognitive agent.
    
    Attributes:
        perception: Supported perception types.
        reasoning: Supported reasoning modes.
        memory: Supported memory types.
        knowledge: Supported knowledge operations.
        planning: Supported planning operations.
        execution: Supported execution operations.
        learning: Supported learning operations.
        meta_cognition: Supported meta-cognition operations.
    """

    perception: Set[str] = field(default_factory=set)
    reasoning: Set[str] = field(default_factory=set)
    memory: Set[str] = field(default_factory=set)
    knowledge: Set[str] = field(default_factory=set)
    planning: Set[str] = field(default_factory=set)
    execution: Set[str] = field(default_factory=set)
    learning: Set[str] = field(default_factory=set)
    meta_cognition: Set[str] = field(default_factory=set)

    def add_capability(self, category: str, capability: str) -> None:
        """Add a capability to a category."""
        if hasattr(self, category):
            getattr(self, category).add(capability)

    def has_capability(self, category: str, capability: str) -> bool:
        """Check if agent has a specific capability."""
        if hasattr(self, category):
            return capability in getattr(self, category)
        return False

    def get_capabilities(self, category: str = None) -> Set[str]:
        """Get capabilities for a specific category or all categories."""
        if category:
            if hasattr(self, category):
                return getattr(self, category).copy()
            return set()
        else:
            all_caps = set()
            for cat in ["perception", "reasoning", "memory", "knowledge", 
                       "planning", "execution", "learning", "meta_cognition"]:
                if hasattr(self, cat):
                    all_caps.update(getattr(self, cat))
            return all_caps

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "perception": list(self.perception),
            "reasoning": list(self.reasoning),
            "memory": list(self.memory),
            "knowledge": list(self.knowledge),
            "planning": list(self.planning),
            "execution": list(self.execution),
            "learning": list(self.learning),
            "meta_cognition": list(self.meta_cognition),
        }


class CognitiveAgent:
    """
    The main class for the AI Cognitive System.
    
    The CognitiveAgent integrates all cognitive modules and provides a unified
    interface for processing inputs and generating outputs. It follows the
    cognitive loop to process inputs through a series of cognitive stages.
    
    Features:
    - Multi-modal perception (text, voice, images, documents, etc.)
    - Intelligent attention and focus management
    - Multi-layered context management
    - Memory integration (working, short-term, long-term, episodic, semantic)
    - Knowledge integration (search, ranking, fusion, verification)
    - Multi-mode reasoning (deductive, inductive, abductive, analogical, etc.)
    - Hierarchical planning and goal decomposition
    - Decision making with utility, risk, and confidence evaluation
    - Continuous learning and improvement
    - Tool and skill selection
    - Action execution
    - Outcome evaluation and confidence estimation
    - Self-monitoring and meta-cognition
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.cognitive_system import CognitiveAgent, CognitiveConfig
        >>> 
        >>> # Create a cognitive agent
        >>> config = CognitiveConfig(
        ...     agent_id="my_agent",
        ...     agent_name="My Agent",
        ...     profile="analytical",
        ... )
        >>> agent = CognitiveAgent(config)
        >>> 
        >>> # Initialize the agent
        >>> await agent.initialize()
        >>> 
        >>> # Process an input
        >>> input_data = {
        ...     "type": "text",
        ...     "content": "Hello, how are you?",
        ...     "metadata": {"source": "user"},
        ... }
        >>> output = await agent.process(input_data)
        >>> 
        >>> # Get agent information
        >>> info = agent.get_info()
        >>> 
        >>> # Stop the agent
        >>> await agent.stop()
    """

    def __init__(
        self,
        config: Optional["CognitiveConfig"] = None,
        profile: Optional[Union[str, "CognitiveProfile"]] = None,
    ):
        """
        Initialize the cognitive agent.
        
        Args:
            config: Cognitive configuration.
            profile: Cognitive profile (name or profile object).
        """
        self._config = config
        self._profile: Optional["CognitiveProfile"] = None
        self._initialized = False
        self._started = False
        self._stopped = True
        
        # Cognitive components
        self._state: Optional["CognitiveState"] = None
        self._loop: Optional["CognitiveLoop"] = None
        
        # Cognitive engines
        self._perception_engine: Optional["PerceptionEngine"] = None
        self._attention_engine: Optional["AttentionEngine"] = None
        self._context_engine: Optional["ContextEngine"] = None
        self._reasoning_engine: Optional["ReasoningEngine"] = None
        self._planning_engine: Optional["PlanningEngine"] = None
        self._reflection_engine: Optional["ReflectionEngine"] = None
        self._decision_engine: Optional["DecisionEngine"] = None
        self._learning_engine: Optional["LearningEngine"] = None
        
        # Memory interfaces
        self._working_memory: Optional["WorkingMemory"] = None
        self._long_term_memory: Optional["LongTermMemoryInterface"] = None
        
        # Knowledge interface
        self._knowledge_interface: Optional["KnowledgeInterface"] = None
        
        # Execution engines
        self._skill_selection_engine: Optional["SkillSelectionEngine"] = None
        self._tool_selection_engine: Optional["ToolSelectionEngine"] = None
        self._action_executor: Optional["ActionExecutor"] = None
        
        # Evaluation engines
        self._evaluation_engine: Optional["EvaluationEngine"] = None
        self._confidence_engine: Optional["ConfidenceEngine"] = None
        
        # Meta-cognition engines
        self._self_monitoring_engine: Optional["SelfMonitoringEngine"] = None
        self._meta_cognition_engine: Optional["MetaCognitionEngine"] = None
        
        # Goal manager
        self._goal_manager: Optional["GoalManager"] = None
        
        # Capabilities
        self._capabilities = AgentCapabilities()
        
        # Set profile
        if profile:
            self.set_profile(profile)
        
        # Set config from profile if not provided
        if config is None and self._profile:
            self._config = self._profile.to_config()
        
        logger.info(f"CognitiveAgent initialized: {self._config.agent_id if self._config else 'unknown'}")

    @property
    def config(self) -> "CognitiveConfig":
        """Get the cognitive configuration."""
        if self._config is None:
            from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
            self._config = CognitiveConfig(agent_id="default")
        return self._config

    @config.setter
    def config(self, value: "CognitiveConfig") -> None:
        """Set the cognitive configuration."""
        self._config = value

    @property
    def profile(self) -> Optional["CognitiveProfile"]:
        """Get the cognitive profile."""
        return self._profile

    @property
    def state(self) -> "CognitiveState":
        """Get the cognitive state."""
        if self._state is None:
            from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
            self._state = CognitiveState(self._config)
        return self._state

    @property
    def loop(self) -> "CognitiveLoop":
        """Get the cognitive loop."""
        if self._loop is None:
            from tangku_agentos.cognitive_system.core.cognitive_loop import CognitiveLoop
            self._loop = CognitiveLoop(self._state, self._config)
        return self._loop

    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the agent is started."""
        return self._started

    @property
    def is_stopped(self) -> bool:
        """Check if the agent is stopped."""
        return self._stopped

    @property
    def capabilities(self) -> AgentCapabilities:
        """Get the agent's capabilities."""
        return self._capabilities

    # Perception Engine
    @property
    def perception(self) -> "PerceptionEngine":
        """Get the perception engine."""
        if self._perception_engine is None:
            from tangku_agentos.cognitive_system.engines.perception import PerceptionEngine
            self._perception_engine = PerceptionEngine(self.config, self.state)
        return self._perception_engine

    # Attention Engine
    @property
    def attention(self) -> "AttentionEngine":
        """Get the attention engine."""
        if self._attention_engine is None:
            from tangku_agentos.cognitive_system.engines.attention import AttentionEngine
            self._attention_engine = AttentionEngine(self.config, self.state)
        return self._attention_engine

    # Context Engine
    @property
    def context(self) -> "ContextEngine":
        """Get the context engine."""
        if self._context_engine is None:
            from tangku_agentos.cognitive_system.engines.context import ContextEngine
            self._context_engine = ContextEngine(self.config, self.state)
        return self._context_engine

    # Reasoning Engine
    @property
    def reasoning(self) -> "ReasoningEngine":
        """Get the reasoning engine."""
        if self._reasoning_engine is None:
            from tangku_agentos.cognitive_system.engines.reasoning import ReasoningEngine
            self._reasoning_engine = ReasoningEngine(self.config, self.state)
        return self._reasoning_engine

    # Planning Engine
    @property
    def planning(self) -> "PlanningEngine":
        """Get the planning engine."""
        if self._planning_engine is None:
            from tangku_agentos.cognitive_system.engines.planning import PlanningEngine
            self._planning_engine = PlanningEngine(self.config, self.state)
        return self._planning_engine

    # Reflection Engine
    @property
    def reflection(self) -> "ReflectionEngine":
        """Get the reflection engine."""
        if self._reflection_engine is None:
            from tangku_agentos.cognitive_system.engines.reflection import ReflectionEngine
            self._reflection_engine = ReflectionEngine(self.config, self.state)
        return self._reflection_engine

    # Decision Engine
    @property
    def decision(self) -> "DecisionEngine":
        """Get the decision engine."""
        if self._decision_engine is None:
            from tangku_agentos.cognitive_system.engines.decision import DecisionEngine
            self._decision_engine = DecisionEngine(self.config, self.state)
        return self._decision_engine

    # Learning Engine
    @property
    def learning(self) -> "LearningEngine":
        """Get the learning engine."""
        if self._learning_engine is None:
            from tangku_agentos.cognitive_system.engines.learning import LearningEngine
            self._learning_engine = LearningEngine(self.config, self.state)
        return self._learning_engine

    # Working Memory
    @property
    def working_memory(self) -> "WorkingMemory":
        """Get the working memory."""
        if self._working_memory is None:
            from tangku_agentos.cognitive_system.memory.working_memory import WorkingMemory
            self._working_memory = WorkingMemory(self.config, self.state)
        return self._working_memory

    # Long-Term Memory
    @property
    def long_term_memory(self) -> "LongTermMemoryInterface":
        """Get the long-term memory interface."""
        if self._long_term_memory is None:
            from tangku_agentos.cognitive_system.memory.long_term_memory import LongTermMemoryInterface
            self._long_term_memory = LongTermMemoryInterface(self.config, self.state)
        return self._long_term_memory

    # Knowledge Interface
    @property
    def knowledge(self) -> "KnowledgeInterface":
        """Get the knowledge interface."""
        if self._knowledge_interface is None:
            from tangku_agentos.cognitive_system.knowledge.knowledge_interface import KnowledgeInterface
            self._knowledge_interface = KnowledgeInterface(self.config, self.state)
        return self._knowledge_interface

    # Skill Selection Engine
    @property
    def skill_selection(self) -> "SkillSelectionEngine":
        """Get the skill selection engine."""
        if self._skill_selection_engine is None:
            from tangku_agentos.cognitive_system.execution.skill_selection import SkillSelectionEngine
            self._skill_selection_engine = SkillSelectionEngine(self.config, self.state)
        return self._skill_selection_engine

    # Tool Selection Engine
    @property
    def tool_selection(self) -> "ToolSelectionEngine":
        """Get the tool selection engine."""
        if self._tool_selection_engine is None:
            from tangku_agentos.cognitive_system.execution.tool_selection import ToolSelectionEngine
            self._tool_selection_engine = ToolSelectionEngine(self.config, self.state)
        return self._tool_selection_engine

    # Action Executor
    @property
    def action_executor(self) -> "ActionExecutor":
        """Get the action executor."""
        if self._action_executor is None:
            from tangku_agentos.cognitive_system.execution.action_executor import ActionExecutor
            self._action_executor = ActionExecutor(self.config, self.state)
        return self._action_executor

    # Evaluation Engine
    @property
    def evaluation(self) -> "EvaluationEngine":
        """Get the evaluation engine."""
        if self._evaluation_engine is None:
            from tangku_agentos.cognitive_system.evaluation.evaluation_engine import EvaluationEngine
            self._evaluation_engine = EvaluationEngine(self.config, self.state)
        return self._evaluation_engine

    # Confidence Engine
    @property
    def confidence(self) -> "ConfidenceEngine":
        """Get the confidence engine."""
        if self._confidence_engine is None:
            from tangku_agentos.cognitive_system.evaluation.confidence_engine import ConfidenceEngine
            self._confidence_engine = ConfidenceEngine(self.config, self.state)
        return self._confidence_engine

    # Self-Monitoring Engine
    @property
    def self_monitoring(self) -> "SelfMonitoringEngine":
        """Get the self-monitoring engine."""
        if self._self_monitoring_engine is None:
            from tangku_agentos.cognitive_system.meta.self_monitoring import SelfMonitoringEngine
            self._self_monitoring_engine = SelfMonitoringEngine(self.config, self.state)
        return self._self_monitoring_engine

    # Meta-Cognition Engine
    @property
    def meta_cognition(self) -> "MetaCognitionEngine":
        """Get the meta-cognition engine."""
        if self._meta_cognition_engine is None:
            from tangku_agentos.cognitive_system.meta.meta_cognition import MetaCognitionEngine
            self._meta_cognition_engine = MetaCognitionEngine(self.config, self.state)
        return self._meta_cognition_engine

    # Goal Manager
    @property
    def goals(self) -> "GoalManager":
        """Get the goal manager."""
        if self._goal_manager is None:
            from tangku_agentos.cognitive_system.goals.goal_manager import GoalManager
            self._goal_manager = GoalManager(self.config, self.state)
        return self._goal_manager

    def set_profile(self, profile: Union[str, "CognitiveProfile"]) -> None:
        """
        Set the cognitive profile for the agent.
        
        Args:
            profile: Cognitive profile (name or profile object).
        """
        from tangku_agentos.cognitive_system.core.cognitive_profile import get_profile
        
        if isinstance(profile, str):
            self._profile = get_profile(profile)
        else:
            self._profile = profile
        
        # Update config from profile
        if self._profile and not self._config:
            self._config = self._profile.to_config()
        
        logger.info(f"Cognitive profile set: {self._profile.name if self._profile else 'unknown'}")

    async def initialize(self) -> None:
        """
        Initialize the cognitive agent.
        
        This method initializes all cognitive components and prepares
        the agent for processing inputs.
        """
        if self._initialized:
            logger.warning("CognitiveAgent already initialized")
            return
        
        logger.info(f"Initializing CognitiveAgent: {self.config.agent_id}")
        
        try:
            # Initialize state
            self.state.config = self.config
            await self.state.initialize()
            
            # Initialize loop
            self.loop.state = self.state
            self.loop.config = self.config
            await self.loop.initialize()
            
            # Register stage handlers
            await self._register_stage_handlers()
            
            # Initialize all engines
            await self._initialize_engines()
            
            # Update capabilities
            self._update_capabilities()
            
            # Mark as initialized
            self._initialized = True
            self._stopped = False
            
            logger.info(f"CognitiveAgent initialized: {self.config.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CognitiveAgent: {e}")
            raise

    async def _register_stage_handlers(self) -> None:
        """Register handlers for each cognitive stage."""
        # PERCEIVE
        self.loop.register_stage_handler("PERCEIVE", self._handle_perceive)
        
        # UNDERSTAND_CONTEXT
        self.loop.register_stage_handler("UNDERSTAND_CONTEXT", self._handle_understand_context)
        
        # RETRIEVE_MEMORY
        self.loop.register_stage_handler("RETRIEVE_MEMORY", self._handle_retrieve_memory)
        
        # RETRIEVE_KNOWLEDGE
        self.loop.register_stage_handler("RETRIEVE_KNOWLEDGE", self._handle_retrieve_knowledge)
        
        # REASON
        self.loop.register_stage_handler("REASON", self._handle_reason)
        
        # PLAN
        self.loop.register_stage_handler("PLAN", self._handle_plan)
        
        # EVALUATE_OPTIONS
        self.loop.register_stage_handler("EVALUATE_OPTIONS", self._handle_evaluate_options)
        
        # SELECT_TOOLS
        self.loop.register_stage_handler("SELECT_TOOLS", self._handle_select_tools)
        
        # EXECUTE
        self.loop.register_stage_handler("EXECUTE", self._handle_execute)
        
        # OBSERVE_RESULTS
        self.loop.register_stage_handler("OBSERVE_RESULTS", self._handle_observe_results)
        
        # REFLECT
        self.loop.register_stage_handler("REFLECT", self._handle_reflect)
        
        # LEARN
        self.loop.register_stage_handler("LEARN", self._handle_learn)
        
        # UPDATE_MEMORY
        self.loop.register_stage_handler("UPDATE_MEMORY", self._handle_update_memory)
        
        # CONTINUE
        self.loop.register_stage_handler("CONTINUE", self._handle_continue)

    async def _initialize_engines(self) -> None:
        """Initialize all cognitive engines."""
        # Initialize engines that need initialization
        if self.config.memory.enabled:
            await self.working_memory.initialize()
            await self.long_term_memory.initialize()
        
        if self.config.knowledge.enabled:
            await self.knowledge.initialize()
        
        if self.config.reasoning.can_handle_commands:
            await self.reasoning.initialize()
        
        if self.config.planning.can_execute_tasks:
            await self.planning.initialize()
        
        if self.config.learning.can_execute_tasks:
            await self.learning.initialize()
        
        if self.config.meta_cognition.can_execute_tasks:
            await self.meta_cognition.initialize()

    def _update_capabilities(self) -> None:
        """Update the agent's capabilities based on configuration."""
        # Perception capabilities
        if self.config.enabled_modules:
            if "perception" in self.config.enabled_modules:
                self._capabilities.perception.update([
                    "text", "voice", "images", "documents",
                    "repositories", "terminal_output", "runtime_events",
                    "system_events", "workspace_changes", "sensor_events",
                ])
        
        # Reasoning capabilities
        if "reasoning" in self.config.enabled_modules:
            self._capabilities.reasoning.update([
                "deductive", "inductive", "abductive", "analogical",
                "probabilistic", "causal", "counterfactual", "mathematical",
                "symbolic", "chain_of_thought", "tree_of_thought",
                "graph_reasoning", "multi_agent_reasoning",
            ])
        
        # Memory capabilities
        if "working_memory" in self.config.enabled_modules:
            self._capabilities.memory.add("working_memory")
        if "long_term_memory" in self.config.enabled_modules:
            self._capabilities.memory.add("long_term_memory")
        if "episodic_memory" in self.config.enabled_modules:
            self._capabilities.memory.add("episodic_memory")
        if "semantic_memory" in self.config.enabled_modules:
            self._capabilities.memory.add("semantic_memory")
        
        # Knowledge capabilities
        if "knowledge" in self.config.enabled_modules:
            self._capabilities.knowledge.update([
                "search", "ranking", "fusion", "verification",
                "extraction", "linking", "updates", "confidence",
            ])
        
        # Planning capabilities
        if "planning" in self.config.enabled_modules:
            self._capabilities.planning.update([
                "goal_decomposition", "hierarchical_planning",
                "task_graphs", "dependency_graphs", "execution_plans",
                "parallel_plans", "adaptive_replanning", "rollback_plans",
                "recovery_plans",
            ])
        
        # Execution capabilities
        if "tool_selection" in self.config.enabled_modules:
            self._capabilities.execution.add("tool_selection")
        if "skill_selection" in self.config.enabled_modules:
            self._capabilities.execution.add("skill_selection")
        if "action_executor" in self.config.enabled_modules:
            self._capabilities.execution.add("action_execution")
        
        # Learning capabilities
        if "learning" in self.config.enabled_modules:
            self._capabilities.learning.update([
                "experience_learning", "pattern_learning",
                "skill_learning", "failure_learning",
                "success_reinforcement", "feedback_integration",
                "preference_learning", "memory_optimization",
                "knowledge_refinement",
            ])
        
        # Meta-cognition capabilities
        if "self_monitoring" in self.config.enabled_modules:
            self._capabilities.meta_cognition.add("self_monitoring")
        if "meta_cognition" in self.config.enabled_modules:
            self._capabilities.meta_cognition.add("meta_cognition")

    async def start(self) -> None:
        """
        Start the cognitive agent.
        
        This method starts the cognitive loop and prepares the agent
        to process inputs.
        """
        if self._started:
            logger.warning("CognitiveAgent already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Starting CognitiveAgent: {self.config.agent_id}")
        
        try:
            # Start the loop
            await self.loop.start()
            
            # Start all engines that need to be started
            if self.config.memory.enabled:
                await self.working_memory.start()
                await self.long_term_memory.start()
            
            if self.config.knowledge.enabled:
                await self.knowledge.start()
            
            if self.config.meta_cognition.can_execute_tasks:
                await self.meta_cognition.start()
            
            # Mark as started
            self._started = True
            self._stopped = False
            
            logger.info(f"CognitiveAgent started: {self.config.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to start CognitiveAgent: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the cognitive agent.
        
        This method stops the cognitive loop and all cognitive components.
        """
        if self._stopped:
            logger.warning("CognitiveAgent already stopped")
            return
        
        logger.info(f"Stopping CognitiveAgent: {self.config.agent_id}")
        
        try:
            # Stop the loop
            await self.loop.stop()
            
            # Stop all engines
            if self.config.memory.enabled:
                await self.working_memory.stop()
                await self.long_term_memory.stop()
            
            if self.config.knowledge.enabled:
                await self.knowledge.stop()
            
            if self.config.meta_cognition.can_execute_tasks:
                await self.meta_cognition.stop()
            
            # Mark as stopped
            self._started = False
            self._stopped = True
            
            logger.info(f"CognitiveAgent stopped: {self.config.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop CognitiveAgent: {e}")
            raise

    async def pause(self) -> None:
        """Pause the cognitive agent."""
        await self.loop.pause()
        logger.info(f"CognitiveAgent paused: {self.config.agent_id}")

    async def resume(self) -> None:
        """Resume the cognitive agent."""
        await self.loop.resume()
        logger.info(f"CognitiveAgent resumed: {self.config.agent_id}")

    async def process(
        self,
        input_data: Any,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Process an input through the cognitive loop.
        
        Args:
            input_data: Input data to process.
            timeout: Timeout for processing.
        
        Returns:
            Output from the cognitive loop.
        """
        if not self._started:
            await self.start()
        
        # Process through the loop
        return await self.loop.process(input_data, timeout)

    async def process_batch(
        self,
        inputs: List[Any],
        timeout: Optional[float] = None,
    ) -> List[Any]:
        """
        Process multiple inputs through the cognitive loop.
        
        Args:
            inputs: List of input data to process.
            timeout: Timeout for each input.
        
        Returns:
            List of outputs from the cognitive loop.
        """
        outputs = []
        for input_data in inputs:
            output = await self.process(input_data, timeout)
            outputs.append(output)
        return outputs

    # Stage Handlers

    async def _handle_perceive(self) -> Any:
        """Handle the PERCEIVE stage."""
        input_data = self.state.context.current_input
        
        # Process input through perception engine
        perceived = await self.perception.process(input_data)
        
        # Store in working memory
        await self.working_memory.store("perceived_input", perceived)
        
        # Update context
        self.state.context.current_input = perceived
        
        return perceived

    async def _handle_understand_context(self) -> Any:
        """Handle the UNDERSTAND_CONTEXT stage."""
        perceived = self.state.context.current_input
        
        # Process through attention engine
        focused = await self.attention.focus(perceived)
        
        # Process through context engine
        context = await self.context.understand(focused)
        
        # Update state context
        self.state.context.attention_focus = focused.get("focus", [])
        self.state.context.execution_context = context.get("context", {})
        
        return context

    async def _handle_retrieve_memory(self) -> Any:
        """Handle the RETRIEVE_MEMORY stage."""
        context = self.state.context.execution_context
        focus = self.state.context.attention_focus
        
        # Retrieve from working memory
        working_memories = await self.working_memory.retrieve(context, limit=10)
        
        # Retrieve from long-term memory
        long_term_memories = []
        if self.config.memory.long_term_memory_enabled:
            long_term_memories = await self.long_term_memory.retrieve(context, limit=10)
        
        # Combine memories
        all_memories = working_memories + long_term_memories
        
        # Store relevant memories in context
        self.state.context.relevant_memories = all_memories
        
        return {"memories": all_memories}

    async def _handle_retrieve_knowledge(self) -> Any:
        """Handle the RETRIEVE_KNOWLEDGE stage."""
        context = self.state.context.execution_context
        memories = self.state.context.relevant_memories
        
        # Retrieve knowledge based on context and memories
        knowledge = await self.knowledge.retrieve(context, limit=10)
        
        # Store relevant knowledge in context
        self.state.context.relevant_knowledge = knowledge.get("results", [])
        
        return knowledge

    async def _handle_reason(self) -> Any:
        """Handle the REASON stage."""
        context = self.state.context.execution_context
        memories = self.state.context.relevant_memories
        knowledge = self.state.context.relevant_knowledge
        
        # Process through reasoning engine
        reasoning_result = await self.reasoning.reason(
            context=context,
            memories=memories,
            knowledge=knowledge,
        )
        
        return reasoning_result

    async def _handle_plan(self) -> Any:
        """Handle the PLAN stage."""
        reasoning_result = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Process through planning engine
        planning_result = await self.planning.plan(
            goal=context.get("goal"),
            reasoning=reasoning_result,
            context=context,
        )
        
        return planning_result

    async def _handle_evaluate_options(self) -> Any:
        """Handle the EVALUATE_OPTIONS stage."""
        planning_result = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Process through decision engine
        decision_result = await self.decision.evaluate_options(
            options=planning_result.get("options", []),
            context=context,
        )
        
        return decision_result

    async def _handle_select_tools(self) -> Any:
        """Handle the SELECT_TOOLS stage."""
        decision_result = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Select tools based on decision
        selected_tools = await self.tool_selection.select(
            task=decision_result.get("selected_option"),
            context=context,
        )
        
        # Select skills if needed
        selected_skills = []
        if self.config.execution.skill_selection_enabled:
            selected_skills = await self.skill_selection.select(
                task=decision_result.get("selected_option"),
                context=context,
            )
        
        return {
            "tools": selected_tools,
            "skills": selected_skills,
        }

    async def _handle_execute(self) -> Any:
        """Handle the EXECUTE stage."""
        selection = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Execute actions through action executor
        execution_result = await self.action_executor.execute(
            tools=selection.get("tools", []),
            skills=selection.get("skills", []),
            context=context,
        )
        
        return execution_result

    async def _handle_observe_results(self) -> Any:
        """Handle the OBSERVE_RESULTS stage."""
        execution_result = self.state.context.current_output
        
        # Observe and record results
        observation = {
            "results": execution_result.get("results", []),
            "success": execution_result.get("success", False),
            "errors": execution_result.get("errors", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Store observation in working memory
        await self.working_memory.store("last_observation", observation)
        
        return observation

    async def _handle_reflect(self) -> Any:
        """Handle the REFLECT stage."""
        observation = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Process through reflection engine
        reflection_result = await self.reflection.reflect(
            observation=observation,
            context=context,
        )
        
        return reflection_result

    async def _handle_learn(self) -> Any:
        """Handle the LEARN stage."""
        reflection_result = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Process through learning engine
        learning_result = await self.learning.learn(
            reflection=reflection_result,
            context=context,
        )
        
        return learning_result

    async def _handle_update_memory(self) -> Any:
        """Handle the UPDATE_MEMORY stage."""
        learning_result = self.state.context.current_output
        context = self.state.context.execution_context
        
        # Update working memory
        await self.working_memory.update(learning_result)
        
        # Update long-term memory if enabled
        if self.config.memory.long_term_memory_enabled:
            await self.long_term_memory.update(learning_result)
        
        return {"status": "memory_updated"}

    async def _handle_continue(self) -> Any:
        """Handle the CONTINUE stage."""
        # Prepare for next iteration
        self.state.context.clear_focus()
        self.state.context.clear_relevant_info()
        
        return {"status": "continue"}

    # Direct Engine Access

    async def perceive(self, input_data: Any) -> Any:
        """
        Process input through the perception engine.
        
        Args:
            input_data: Input data to perceive.
        
        Returns:
            Perceived data.
        """
        return await self.perception.process(input_data)

    async def focus_attention(self, data: Any) -> Any:
        """
        Focus attention on specific data.
        
        Args:
            data: Data to focus on.
        
        Returns:
            Focused data.
        """
        return await self.attention.focus(data)

    async def understand_context(self, data: Any) -> Any:
        """
        Understand the context of data.
        
        Args:
            data: Data to understand.
        
        Returns:
            Context understanding.
        """
        return await self.context.understand(data)

    async def reason(self, context: Any, memories: List[Any] = None, knowledge: List[Any] = None) -> Any:
        """
        Apply reasoning to a situation.
        
        Args:
            context: Context for reasoning.
            memories: Relevant memories.
            knowledge: Relevant knowledge.
        
        Returns:
            Reasoning result.
        """
        return await self.reasoning.reason(
            context=context,
            memories=memories or [],
            knowledge=knowledge or [],
        )

    async def plan(self, goal: str, context: Any = None) -> Any:
        """
        Create a plan for achieving a goal.
        
        Args:
            goal: Goal to achieve.
            context: Context for planning.
        
        Returns:
            Planning result.
        """
        return await self.planning.plan(goal=goal, context=context or {})

    async def decide(self, options: List[Any], context: Any = None) -> Any:
        """
        Make a decision among options.
        
        Args:
            options: List of options to choose from.
            context: Context for decision making.
        
        Returns:
            Decision result.
        """
        return await self.decision.decide(options=options, context=context or {})

    async def execute(self, actions: List[Any], context: Any = None) -> Any:
        """
        Execute a list of actions.
        
        Args:
            actions: List of actions to execute.
            context: Context for execution.
        
        Returns:
            Execution result.
        """
        return await self.action_executor.execute(
            tools=actions,
            context=context or {},
        )

    async def reflect(self, observation: Any, context: Any = None) -> Any:
        """
        Reflect on an observation.
        
        Args:
            observation: Observation to reflect on.
            context: Context for reflection.
        
        Returns:
            Reflection result.
        """
        return await self.reflection.reflect(
            observation=observation,
            context=context or {},
        )

    async def learn(self, reflection: Any, context: Any = None) -> Any:
        """
        Learn from a reflection.
        
        Args:
            reflection: Reflection to learn from.
            context: Context for learning.
        
        Returns:
            Learning result.
        """
        return await self.learning.learn(
            reflection=reflection,
            context=context or {},
        )

    # Memory Operations

    async def store_memory(self, key: str, data: Any) -> None:
        """
        Store data in working memory.
        
        Args:
            key: Key for the memory.
            data: Data to store.
        """
        await self.working_memory.store(key, data)

    async def retrieve_memory(self, query: Any, limit: int = 10) -> List[Any]:
        """
        Retrieve memories from working memory.
        
        Args:
            query: Query for retrieval.
            limit: Maximum number of memories to retrieve.
        
        Returns:
            List of retrieved memories.
        """
        return await self.working_memory.retrieve(query, limit)

    async def update_memory(self, data: Any) -> None:
        """
        Update memory with new data.
        
        Args:
            data: Data to update memory with.
        """
        await self.working_memory.update(data)

    # Knowledge Operations

    async def search_knowledge(self, query: Any, limit: int = 10) -> List[Any]:
        """
        Search knowledge base.
        
        Args:
            query: Search query.
            limit: Maximum number of results.
        
        Returns:
            List of knowledge results.
        """
        result = await self.knowledge.retrieve(query, limit)
        return result.get("results", [])

    async def update_knowledge(self, data: Any) -> None:
        """
        Update knowledge base.
        
        Args:
            data: Data to update knowledge with.
        """
        await self.knowledge.update(data)

    # Goal Operations

    async def set_goal(self, goal: str, priority: int = 1) -> None:
        """
        Set a goal for the agent.
        
        Args:
            goal: Goal to set.
            priority: Priority of the goal.
        """
        await self.goals.set_goal(goal, priority)

    async def get_goals(self) -> List[Any]:
        """
        Get the agent's current goals.
        
        Returns:
            List of current goals.
        """
        return await self.goals.get_goals()

    async def complete_goal(self, goal_id: str) -> None:
        """
        Mark a goal as completed.
        
        Args:
            goal_id: ID of the goal to complete.
        """
        await self.goals.complete_goal(goal_id)

    # Information Methods

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dictionary with agent information.
        """
        return {
            "agent_id": self.config.agent_id,
            "agent_name": self.config.agent_name,
            "agent_version": self.config.agent_version,
            "profile": self._profile.name if self._profile else None,
            "initialized": self._initialized,
            "started": self._started,
            "stopped": self._stopped,
            "capabilities": self._capabilities.to_dict(),
            "state": self.state.get_state_info(),
            "loop": self.loop.get_status_info(),
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary with status information.
        """
        return {
            "initialized": self._initialized,
            "started": self._started,
            "stopped": self._stopped,
            "state": self.state.state.name,
            "stage": self.state.stage.name,
            "loop_mode": self.loop.mode.name,
            "loop_status": self.loop.status.name,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the agent.
        
        Returns:
            Dictionary with metrics.
        """
        return {
            "state_metrics": self.state.metrics.get_metrics(),
            "loop_metrics": self.loop.metrics.get_metrics(),
        }

    def reset(self) -> None:
        """Reset the cognitive agent."""
        self._initialized = False
        self._started = False
        self._stopped = True
        self._state.reset()
        self._loop.reset()
        logger.info(f"CognitiveAgent reset: {self.config.agent_id}")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CognitiveAgent("
            f"id={self.config.agent_id}, "
            f"name={self.config.agent_name}, "
            f"initialized={self._initialized}, "
            f"started={self._started})"
        )
