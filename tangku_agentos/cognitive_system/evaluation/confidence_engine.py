"""Confidence Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class ConfidenceResult:
    confidence_id: str; target: Any; confidence: float=0.0
    breakdown: Dict[str, float]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class ConfidenceEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._metrics={"calculations":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def calculate(
        self,
        target: Any,
        context: Optional[Dict[str, Any]]=None
    ) -> ConfidenceResult:
        """Calculate confidence score for a target."""
        from tangku_agentos.cognitive_system.exceptions import ConfidenceError
        try:
            # Calculate confidence from different sources
            reasoning_conf=self._calculate_reasoning_confidence(target, context)
            knowledge_conf=self._calculate_knowledge_confidence(target, context)
            memory_conf=self._calculate_memory_confidence(target, context)
            tool_conf=self._calculate_tool_confidence(target, context)
            
            breakdown={
                "reasoning": reasoning_conf,
                "knowledge": knowledge_conf,
                "memory": memory_conf,
                "tool": tool_conf
            }
            
            # Get weights from configuration
            weights=self._get_confidence_weights()
            
            # Calculate weighted confidence
            confidence=(
                weights.get("reasoning", 0.4)*reasoning_conf +
                weights.get("knowledge", 0.3)*knowledge_conf +
                weights.get("memory", 0.2)*memory_conf +
                weights.get("tool", 0.1)*tool_conf
            )
            
            result=ConfidenceResult(
                confidence_id=self._generate_id(),
                target=target,
                confidence=confidence,
                breakdown=breakdown
            )
            
            self._metrics["calculations"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise ConfidenceError(f"Confidence calculation failed: {e}") from e
    
    def _generate_id(self) -> str:
        import hashlib
        return f"conf_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _get_confidence_weights(self) -> Dict[str, float]:
        """Get confidence weights from configuration."""
        if self._config and hasattr(self._config, 'evaluation'):
            return self._config.evaluation.confidence_weights
        return {"reasoning": 0.4, "knowledge": 0.3, "memory": 0.2, "tool": 0.1}
    
    def _calculate_reasoning_confidence(self, target: Any, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence from reasoning quality."""
        target_str=str(target).lower()
        
        # Check for confidence indicators
        if "certain" in target_str or "definitely" in target_str:
            return 0.9
        elif "probably" in target_str or "likely" in target_str:
            return 0.7
        elif "maybe" in target_str or "possibly" in target_str:
            return 0.5
        elif "uncertain" in target_str or "unknown" in target_str:
            return 0.2
        
        return 0.6
    
    def _calculate_knowledge_confidence(self, target: Any, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence from knowledge quality."""
        # Check if knowledge is verified
        if isinstance(target, dict) and target.get("verified", False):
            return 0.9
        
        # Check for source reliability
        if isinstance(target, dict):
            source=target.get("source", "")
            if "trusted" in source.lower() or "verified" in source.lower():
                return 0.8
        
        return 0.6
    
    def _calculate_memory_confidence(self, target: Any, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence from memory quality."""
        # Check if memory is recent
        if isinstance(target, dict) and "timestamp" in target:
            timestamp=target["timestamp"]
            if isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    mem_time=datetime.fromisoformat(timestamp)
                    age=(datetime.utcnow()-mem_time).total_seconds()
                    if age<3600:  # Less than 1 hour
                        return 0.9
                    elif age<86400:  # Less than 1 day
                        return 0.7
                    elif age<604800:  # Less than 1 week
                        return 0.5
                except:
                    pass
        
        return 0.6
    
    def _calculate_tool_confidence(self, target: Any, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence from tool reliability."""
        # Check if tool is reliable
        if isinstance(target, dict) and target.get("reliable", False):
            return 0.9
        
        return 0.7
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
