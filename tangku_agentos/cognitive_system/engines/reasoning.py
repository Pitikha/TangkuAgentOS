"""AI Cognitive System - Reasoning Engine"""
from __future__ import annotations
import asyncio, logging, random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class ReasoningMode(Enum):
    DEDUCTIVE=auto(); INDUCTIVE=auto(); ABDUCTIVE=auto(); ANALOGICAL=auto()
    PROBABILISTIC=auto(); CAUSAL=auto(); COUNTERFACTUAL=auto(); MATHEMATICAL=auto()
    SYMBOLIC=auto(); CHAIN_OF_THOUGHT=auto(); TREE_OF_THOUGHT=auto()
    GRAPH=auto(); MULTI_AGENT=auto()

@dataclass
class ReasoningStep:
    step_id: str; step_type: str; content: Any
    inputs: List[Any]=field(default_factory=list); outputs: List[Any]=field(default_factory=list)
    confidence: float=1.0; timestamp: datetime=field(default_factory=datetime.utcnow)

@dataclass
class ReasoningResult:
    result_id: str; reasoning_mode: ReasoningMode; input: Any
    output: Any; steps: List[ReasoningStep]=field(default_factory=list)
    intermediate_results: List[Any]=field(default_factory=list)
    confidence: float=0.0; sources: List[str]=field(default_factory=list)
    timestamp: datetime=field(default_factory=datetime.utcnow); duration: float=0.0

class ReasoningEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._reasoning_modes: Dict[str, Any]={}; self._metrics={"reasoning_operations":0,"errors":0}
    
    async def initialize(self)->None:
        if self._initialized: return
        self._register_reasoning_modes()
        self._initialized=True
    
    async def start(self)->None:
        if self._started: return
        if not self._initialized: await self.initialize()
        self._started=True
    
    async def stop(self)->None:
        if not self._started: return
        self._started=False
    
    def _register_reasoning_modes(self) -> None:
        """Register all reasoning mode handlers."""
        self._reasoning_modes={
            "deductive": self._deductive_reasoning,
            "inductive": self._inductive_reasoning,
            "abductive": self._abductive_reasoning,
            "analogical": self._analogical_reasoning,
            "probabilistic": self._probabilistic_reasoning,
            "causal": self._causal_reasoning,
            "counterfactual": self._counterfactual_reasoning,
            "mathematical": self._mathematical_reasoning,
            "symbolic": self._symbolic_reasoning,
            "chain_of_thought": self._chain_of_thought_reasoning,
            "tree_of_thought": self._tree_of_thought_reasoning,
            "graph": self._graph_reasoning,
            "multi_agent": self._multi_agent_reasoning,
        }
    
    async def reason(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None,
        mode: Optional[ReasoningMode]=None
    ) -> ReasoningResult:
        """Perform reasoning on the given context."""
        from tangku_agentos.cognitive_system.exceptions import ReasoningError
        import time
        start_time=time.time()
        
        try:
            # Determine reasoning mode
            actual_mode=mode or self._get_default_mode()
            
            # Get reasoning function
            reason_func=self._reasoning_modes.get(actual_mode.name.lower(), self._default_reasoning)
            
            # Perform reasoning
            result=await reason_func(context, memories, knowledge)
            
            # Ensure result has required fields
            if not isinstance(result, ReasoningResult):
                result=ReasoningResult(
                    result_id=self._generate_id(),
                    reasoning_mode=actual_mode,
                    input=context,
                    output=result,
                    duration=time.time()-start_time
                )
            else:
                result.duration=time.time()-start_time
            
            self._metrics["reasoning_operations"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise ReasoningError(f"Reasoning failed: {e}") from e
    
    def _get_default_mode(self) -> ReasoningMode:
        """Get the default reasoning mode from configuration."""
        if self._config and hasattr(self._config, 'reasoning'):
            mode_str=self._config.reasoning.mode.value if hasattr(self._config.reasoning.mode, 'value') else str(self._config.reasoning.mode)
            try:
                return ReasoningMode[mode_str.upper()]
            except KeyError:
                pass
        return ReasoningMode.CHAIN_OF_THOUGHT
    
    def _generate_id(self) -> str:
        """Generate a unique ID for reasoning result."""
        import hashlib
        return f"reason_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    async def _default_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> Any:
        """Default reasoning handler."""
        return f"Reasoned about: {str(context)[:100]}"
    
    async def _deductive_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> ReasoningResult:
        """Deductive reasoning: from general to specific."""
        steps=[]
        
        # Step 1: Identify premises
        premises=self._extract_premises(context, knowledge)
        step1=ReasoningStep(
            step_id="1", step_type="identify_premises", content=premises,
            confidence=0.9
        )
        steps.append(step1)
        
        # Step 2: Apply logical rules
        conclusions=self._apply_logical_rules(premises)
        step2=ReasoningStep(
            step_id="2", step_type="apply_rules", content=conclusions,
            inputs=[premises], confidence=0.8
        )
        steps.append(step2)
        
        # Step 3: Validate conclusions
        validated=self._validate_conclusions(conclusions, context)
        step3=ReasoningStep(
            step_id="3", step_type="validate", content=validated,
            inputs=[conclusions], confidence=0.7
        )
        steps.append(step3)
        
        return ReasoningResult(
            result_id=self._generate_id(),
            reasoning_mode=ReasoningMode.DEDUCTIVE,
            input=context,
            output=validated,
            steps=steps,
            confidence=0.8
        )
    
    async def _inductive_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> ReasoningResult:
        """Inductive reasoning: from specific to general."""
        steps=[]
        
        # Step 1: Collect observations
        observations=self._collect_observations(context, memories, knowledge)
        step1=ReasoningStep(
            step_id="1", step_type="collect_observations", content=observations,
            confidence=0.8
        )
        steps.append(step1)
        
        # Step 2: Identify patterns
        patterns=self._identify_patterns(observations)
        step2=ReasoningStep(
            step_id="2", step_type="identify_patterns", content=patterns,
            inputs=[observations], confidence=0.7
        )
        steps.append(step2)
        
        # Step 3: Formulate generalizations
        generalizations=self._formulate_generalizations(patterns)
        step3=ReasoningStep(
            step_id="3", step_type="formulate_generalizations", content=generalizations,
            inputs=[patterns], confidence=0.6
        )
        steps.append(step3)
        
        return ReasoningResult(
            result_id=self._generate_id(),
            reasoning_mode=ReasoningMode.INDUCTIVE,
            input=context,
            output=generalizations,
            steps=steps,
            confidence=0.7
        )
    
    async def _abductive_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> ReasoningResult:
        """Abductive reasoning: infer best explanation."""
        steps=[]
        
        # Step 1: Identify observations
        observations=self._extract_observations(context)
        step1=ReasoningStep(
            step_id="1", step_type="identify_observations", content=observations,
            confidence=0.8
        )
        steps.append(step1)
        
        # Step 2: Generate hypotheses
        hypotheses=self._generate_hypotheses(observations, knowledge)
        step2=ReasoningStep(
            step_id="2", step_type="generate_hypotheses", content=hypotheses,
            inputs=[observations], confidence=0.7
        )
        steps.append(step2)
        
        # Step 3: Evaluate hypotheses
        best_hypothesis=self._evaluate_hypotheses(hypotheses, context, knowledge)
        step3=ReasoningStep(
            step_id="3", step_type="evaluate_hypotheses", content=best_hypothesis,
            inputs=[hypotheses], confidence=0.6
        )
        steps.append(step3)
        
        return ReasoningResult(
            result_id=self._generate_id(),
            reasoning_mode=ReasoningMode.ABDUCTIVE,
            input=context,
            output=best_hypothesis,
            steps=steps,
            confidence=0.6
        )
    
    async def _chain_of_thought_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> ReasoningResult:
        """Chain of Thought reasoning: step-by-step reasoning."""
        steps=[]
        current=context
        
        # Perform multiple reasoning steps
        for i in range(self._config.reasoning.max_depth if self._config else 5):
            # Generate next thought
            next_thought=self._generate_next_thought(current, memories, knowledge, i)
            
            if not next_thought or next_thought==current:
                break
            
            step=ReasoningStep(
                step_id=str(i+1),
                step_type="thought",
                content=next_thought,
                inputs=[current],
                confidence=0.9-(i*0.1)
            )
            steps.append(step)
            current=next_thought
        
        return ReasoningResult(
            result_id=self._generate_id(),
            reasoning_mode=ReasoningMode.CHAIN_OF_THOUGHT,
            input=context,
            output=current,
            steps=steps,
            intermediate_results=[step.content for step in steps[:-1]],
            confidence=0.8
        )
    
    async def _tree_of_thought_reasoning(
        self,
        context: Any,
        memories: Optional[List[Any]]=None,
        knowledge: Optional[List[Any]]=None
    ) -> ReasoningResult:
        """Tree of Thought reasoning: explore multiple paths."""
        from collections import deque
        
        # Initialize with root node
        root={"thought": context, "children": [], "score": 0.0, "depth": 0}
        queue=deque([root])
        best_path=[]
        best_score=-1
        
        max_branches=self._config.reasoning.max_branches if self._config else 3
        max_depth=self._config.reasoning.max_depth if self._config else 3
        
        while queue:
            node=queue.popleft()
            
            if node["depth"]>=max_depth:
                continue
            
            # Generate child thoughts
            children=self._generate_child_thoughts(node["thought"], memories, knowledge, node["depth"])
            
            for child_thought in children[:max_branches]:
                child_node={
                    "thought": child_thought,
                    "children": [],
                    "score": self._score_thought(child_thought, context, knowledge),
                    "depth": node["depth"]+1,
                    "parent": node
                }
                node["children"].append(child_node)
                queue.append(child_node)
                
                # Update best path
                path_score=node["score"] + child_node["score"]
                if path_score>best_score:
                    best_score=path_score
                    best_path=self._reconstruct_path(child_node)
        
        return ReasoningResult(
            result_id=self._generate_id(),
            reasoning_mode=ReasoningMode.TREE_OF_THOUGHT,
            input=context,
            output=best_path[-1] if best_path else context,
            steps=[ReasoningStep(step_id=str(i), step_type="thought", content=t) for i,t in enumerate(best_path)],
            confidence=best_score
        )
    
    def _reconstruct_path(self, node: Dict[str, Any]) -> List[Any]:
        """Reconstruct the path from root to node."""
        path=[]
        current=node
        while current:
            path.insert(0, current["thought"])
            current=current.get("parent")
        return path
    
    def _generate_next_thought(
        self,
        current: Any,
        memories: Optional[List[Any]],
        knowledge: Optional[List[Any]],
        depth: int
    ) -> Any:
        """Generate the next thought in the chain."""
        # Simple implementation: append a reasoning step
        if depth==0:
            return f"Understanding: {current}"
        elif depth==1:
            return f"Analysis: {current}"
        elif depth==2:
            return f"Conclusion: {current}"
        else:
            return f"Step {depth+1}: {current}"
    
    def _generate_child_thoughts(
        self,
        current: Any,
        memories: Optional[List[Any]],
        knowledge: Optional[List[Any]],
        depth: int
    ) -> List[Any]:
        """Generate child thoughts for tree reasoning."""
        # Simple implementation: generate variations
        base=str(current)
        return [
            f"{base} - Option 1",
            f"{base} - Option 2",
            f"{base} - Option 3"
        ]
    
    def _score_thought(self, thought: Any, context: Any, knowledge: Optional[List[Any]]) -> float:
        """Score a thought based on relevance and coherence."""
        # Simple scoring: random for now
        return random.uniform(0.5, 1.0)
    
    def _extract_premises(self, context: Any, knowledge: Optional[List[Any]]) -> List[Any]:
        """Extract premises from context and knowledge."""
        premises=[]
        if isinstance(context, dict):
            for key, value in context.items():
                premises.append(f"{key}: {value}")
        else:
            premises.append(str(context))
        return premises
    
    def _apply_logical_rules(self, premises: List[Any]) -> List[Any]:
        """Apply logical rules to premises."""
        conclusions=[]
        for premise in premises:
            # Simple rule: if premise contains "is", create a conclusion
            if "is" in str(premise).lower():
                conclusions.append(f"Therefore, {premise}")
            else:
                conclusions.append(f"Thus, {premise}")
        return conclusions
    
    def _validate_conclusions(self, conclusions: List[Any], context: Any) -> Any:
        """Validate conclusions against context."""
        # Simple validation: return the first conclusion
        return conclusions[0] if conclusions else "No conclusion"
    
    def _collect_observations(self, context: Any, memories: Optional[List[Any]], knowledge: Optional[List[Any]]) -> List[Any]:
        """Collect observations from context, memories, and knowledge."""
        observations=[]
        
        if isinstance(context, list):
            observations.extend(context)
        else:
            observations.append(context)
        
        if memories:
            observations.extend(memories[:3])  # Limit to 3 memories
        
        if knowledge:
            observations.extend(knowledge[:3])  # Limit to 3 knowledge items
        
        return observations
    
    def _identify_patterns(self, observations: List[Any]) -> List[Any]:
        """Identify patterns in observations."""
        patterns=[]
        for obs in observations:
            patterns.append(f"Pattern in: {str(obs)[:50]}")
        return patterns
    
    def _formulate_generalizations(self, patterns: List[Any]) -> Any:
        """Formulate generalizations from patterns."""
        if not patterns:
            return "No patterns identified"
        return f"Generalization: {patterns[0]}"
    
    def _extract_observations(self, context: Any) -> List[Any]:
        """Extract observations from context."""
        if isinstance(context, list):
            return context
        elif isinstance(context, dict):
            return list(context.values())
        else:
            return [context]
    
    def _generate_hypotheses(self, observations: List[Any], knowledge: Optional[List[Any]]) -> List[Any]:
        """Generate hypotheses to explain observations."""
        hypotheses=[]
        for obs in observations[:3]:  # Limit to 3 observations
            hypotheses.append(f"Hypothesis: {str(obs)[:50]} could be explained by...")
        return hypotheses
    
    def _evaluate_hypotheses(self, hypotheses: List[Any], context: Any, knowledge: Optional[List[Any]]) -> Any:
        """Evaluate and select the best hypothesis."""
        if not hypotheses:
            return "No hypotheses"
        return hypotheses[0]  # Return the first hypothesis
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"ReasoningEngine(initialized={self._initialized}, mode={self._get_default_mode().name})"
