"""AI Cognitive System - Decision Engine"""
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

@dataclass
class DecisionOption:
    option_id: str; description: str; value: Any
    utility: float=0.0; risk: float=0.0; cost: float=0.0; confidence: float=0.0
    permissions: List[str]=field(default_factory=list)
    resources: Dict[str, Any]=field(default_factory=dict)
    constraints: List[str]=field(default_factory=list)

@dataclass
class DecisionResult:
    decision_id: str; options: List[DecisionOption]; selected_option: Optional[DecisionOption]=None
    reasoning: str=""; confidence: float=0.0; utility: float=0.0; risk: float=0.0
    cost: float=0.0; timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class DecisionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._metrics={"decisions_made":0,"errors":0}
    
    async def initialize(self)->None:
        if self._initialized: return
        self._initialized=True
    
    async def start(self)->None:
        if self._started: return
        if not self._initialized: await self.initialize()
        self._started=True
    
    async def stop(self)->None:
        if not self._started: return
        self._started=False
    
    async def decide(
        self,
        options: List[Any],
        context: Optional[Dict[str, Any]]=None
    ) -> DecisionResult:
        """Make a decision among the given options."""
        from tangku_agentos.cognitive_system.exceptions import DecisionError
        import time
        start_time=time.time()
        
        try:
            # Convert options to DecisionOption objects
            decision_options=self._convert_to_decision_options(options)
            
            # Evaluate each option
            evaluated_options=await self._evaluate_options(decision_options, context)
            
            # Select the best option
            selected_option=self._select_best_option(evaluated_options, context)
            
            # Generate reasoning
            reasoning=self._generate_reasoning(evaluated_options, selected_option, context)
            
            # Calculate overall metrics
            utility=selected_option.utility if selected_option else 0.0
            risk=selected_option.risk if selected_option else 0.0
            cost=selected_option.cost if selected_option else 0.0
            confidence=self._calculate_confidence(evaluated_options, selected_option)
            
            # Create decision result
            result=DecisionResult(
                decision_id=self._generate_id(),
                options=evaluated_options,
                selected_option=selected_option,
                reasoning=reasoning,
                confidence=confidence,
                utility=utility,
                risk=risk,
                cost=cost,
                duration=time.time()-start_time
            )
            
            self._metrics["decisions_made"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise DecisionError(f"Decision making failed: {e}") from e
    
    async def evaluate_options(
        self,
        options: List[Any],
        context: Optional[Dict[str, Any]]=None
    ) -> DecisionResult:
        """Evaluate options without selecting one."""
        decision_options=self._convert_to_decision_options(options)
        evaluated_options=await self._evaluate_options(decision_options, context)
        
        return DecisionResult(
            decision_id=self._generate_id(),
            options=evaluated_options,
            reasoning="Options evaluated but no selection made",
            duration=0.0
        )
    
    def _generate_id(self) -> str:
        """Generate a unique decision ID."""
        import hashlib
        return f"dec_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _convert_to_decision_options(self, options: List[Any]) -> List[DecisionOption]:
        """Convert raw options to DecisionOption objects."""
        decision_options=[]
        
        for i, option in enumerate(options):
            if isinstance(option, DecisionOption):
                decision_options.append(option)
            elif isinstance(option, dict):
                decision_option=DecisionOption(
                    option_id=option.get("id", f"opt_{i}"),
                    description=option.get("description", str(option)),
                    value=option.get("value", option),
                    utility=option.get("utility", 0.0),
                    risk=option.get("risk", 0.0),
                    cost=option.get("cost", 0.0),
                    confidence=option.get("confidence", 0.5),
                    permissions=option.get("permissions", []),
                    resources=option.get("resources", {}),
                    constraints=option.get("constraints", [])
                )
                decision_options.append(decision_option)
            else:
                decision_option=DecisionOption(
                    option_id=f"opt_{i}",
                    description=str(option),
                    value=option,
                    confidence=0.5
                )
                decision_options.append(decision_option)
        
        return decision_options
    
    async def _evaluate_options(
        self,
        options: List[DecisionOption],
        context: Optional[Dict[str, Any]]
    ) -> List[DecisionOption]:
        """Evaluate each option based on multiple criteria."""
        evaluated_options=[]
        
        for option in options:
            # Calculate utility
            utility=self._calculate_utility(option, context)
            
            # Calculate risk
            risk=self._calculate_risk(option, context)
            
            # Calculate cost
            cost=self._calculate_cost(option, context)
            
            # Check permissions
            permissions=self._check_permissions(option, context)
            
            # Check resources
            resources=self._check_resources(option, context)
            
            # Check constraints
            constraints=self._check_constraints(option, context)
            
            # Create evaluated option
            evaluated_option=DecisionOption(
                option_id=option.option_id,
                description=option.description,
                value=option.value,
                utility=utility,
                risk=risk,
                cost=cost,
                confidence=option.confidence,
                permissions=permissions,
                resources=resources,
                constraints=constraints
            )
            evaluated_options.append(evaluated_option)
        
        return evaluated_options
    
    def _calculate_utility(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> float:
        """Calculate utility score (0-1) for an option."""
        # Start with base utility
        utility=option.utility if option.utility>0 else 0.5
        
        # Adjust based on context
        if context:
            if "goal" in context:
                # Check if option aligns with goal
                goal=str(context["goal"]).lower()
                description=str(option.description).lower()
                if goal in description:
                    utility+=0.2
            if "preferences" in context:
                # Check if option matches preferences
                preferences=context["preferences"]
                if isinstance(preferences, dict):
                    for key, value in preferences.items():
                        if key in str(option.value):
                            utility+=0.1
        
        return min(1.0, max(0.0, utility))
    
    def _calculate_risk(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> float:
        """Calculate risk score (0-1) for an option."""
        # Start with base risk
        risk=option.risk if option.risk>0 else 0.1
        
        # Adjust based on context
        if context:
            if "risk_tolerance" in context:
                tolerance=context["risk_tolerance"]
                if tolerance=="low":
                    risk*=1.5
                elif tolerance=="high":
                    risk*=0.5
        
        return min(1.0, max(0.0, risk))
    
    def _calculate_cost(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> float:
        """Calculate cost score (0-1) for an option."""
        # Start with base cost
        cost=option.cost if option.cost>0 else 0.1
        
        # Normalize cost
        if cost>1:
            cost=1.0
        
        return min(1.0, max(0.0, cost))
    
    def _check_permissions(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> List[str]:
        """Check permissions for an option."""
        # If no permissions specified, assume allowed
        if not option.permissions:
            return ["allowed"]
        
        # Check against context permissions
        if context and "permissions" in context:
            allowed_permissions=context["permissions"]
            for perm in option.permissions:
                if perm in allowed_permissions:
                    return ["allowed"]
            return ["denied"]
        
        return ["allowed"]
    
    def _check_resources(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check resource availability for an option."""
        # If no resources specified, assume available
        if not option.resources:
            return {"available": True}
        
        # Check against context resources
        if context and "resources" in context:
            available_resources=context["resources"]
            for resource, amount in option.resources.items():
                if resource in available_resources:
                    if available_resources[resource]>=amount:
                        continue
                    else:
                        return {"available": False, "missing": [resource]}
                else:
                    return {"available": False, "missing": [resource]}
            return {"available": True}
        
        return {"available": True}
    
    def _check_constraints(self, option: DecisionOption, context: Optional[Dict[str, Any]]) -> List[str]:
        """Check constraints for an option."""
        # If no constraints, assume satisfied
        if not option.constraints:
            return ["satisfied"]
        
        # Check against context
        if context:
            for constraint in option.constraints:
                if constraint in context:
                    if not context[constraint]:
                        return ["violated"]
            return ["satisfied"]
        
        return ["satisfied"]
    
    def _select_best_option(
        self,
        options: List[DecisionOption],
        context: Optional[Dict[str, Any]]
    ) -> Optional[DecisionOption]:
        """Select the best option based on evaluation criteria."""
        if not options:
            return None
        
        # Filter out invalid options
        valid_options=[opt for opt in options if "allowed" in opt.permissions and opt.resources.get("available", True)]
        
        if not valid_options:
            return None
        
        # Get decision strategy from configuration
        strategy=self._get_decision_strategy()
        
        if strategy=="utility":
            return max(valid_options, key=lambda x: x.utility)
        elif strategy=="risk_averse":
            return min(valid_options, key=lambda x: x.risk)
        elif strategy=="risk_seeking":
            return max(valid_options, key=lambda x: x.risk)
        elif strategy=="cost_based":
            return min(valid_options, key=lambda x: x.cost)
        elif strategy=="balanced":
            # Balanced approach: utility - risk - cost
            return max(valid_options, key=lambda x: x.utility - x.risk*0.3 - x.cost*0.2)
        else:
            # Default: highest utility
            return max(valid_options, key=lambda x: x.utility)
    
    def _get_decision_strategy(self) -> str:
        """Get the decision strategy from configuration."""
        if self._config and hasattr(self._config, 'decision'):
            strategy_str=str(self._config.decision.strategy)
            return strategy_str.lower()
        return "balanced"
    
    def _generate_reasoning(
        self,
        options: List[DecisionOption],
        selected: Optional[DecisionOption],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate reasoning for the decision."""
        if not selected:
            return "No valid option selected"
        
        reasoning=f"Selected option: {selected.description}\n"
        reasoning+=f"Utility: {selected.utility:.2f}, Risk: {selected.risk:.2f}, Cost: {selected.cost:.2f}\n"
        
        if len(options)>1:
            reasoning+="Compared against alternatives:\n"
            for option in options:
                if option.option_id!=selected.option_id:
                    reasoning+=f"  - {option.description}: Utility={option.utility:.2f}, Risk={option.risk:.2f}\n"
        
        return reasoning
    
    def _calculate_confidence(
        self,
        options: List[DecisionOption],
        selected: Optional[DecisionOption]
    ) -> float:
        """Calculate confidence in the decision."""
        if not selected:
            return 0.0
        
        # Confidence based on utility difference
        if len(options)>1:
            other_utilities=[opt.utility for opt in options if opt.option_id!=selected.option_id]
            if other_utilities:
                avg_other=sum(other_utilities)/len(other_utilities)
                utility_diff=selected.utility-avg_other
                confidence=0.5 + (utility_diff*0.5)
            else:
                confidence=selected.confidence
        else:
            confidence=selected.confidence
        
        return min(1.0, max(0.0, confidence))
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"DecisionEngine(initialized={self._initialized}, decisions={self._metrics['decisions_made']})"
