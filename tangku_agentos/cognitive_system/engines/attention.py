"""AI Cognitive System - Attention Engine"""
from __future__ import annotations
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class PriorityLevel(Enum):
    CRITICAL=auto(); HIGH=auto(); NORMAL=auto(); LOW=auto(); BACKGROUND=auto()

@dataclass
class FocusItem:
    item_id: str; content: Any; priority: PriorityLevel=PriorityLevel.NORMAL
    relevance: float=0.0; novelty: float=0.0; urgency: float=0.0; importance: float=0.0
    timestamp: datetime=field(default_factory=datetime.utcnow)

@dataclass
class AttentionResult:
    focused_items: List[FocusItem]; current_focus: Optional[FocusItem]=None
    attention_weights: Dict[str, float]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class AttentionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._focus_items: List[FocusItem]=[]; self._current_focus: Optional[FocusItem]=None
        self._metrics={"focus_switches":0,"items_processed":0,"errors":0}
    
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
    
    async def focus(self, data: Any, context: Optional[Dict[str, Any]]=None) -> AttentionResult:
        """Focus attention on the most relevant items from input data."""
        from tangku_agentos.cognitive_system.exceptions import AttentionError
        try:
            # Convert data to focus items
            items=self._create_focus_items(data, context)
            
            # Score and prioritize items
            scored_items=self._score_items(items, context)
            
            # Select top items based on configuration
            max_focus=self._config.attention.max_focus_items if self._config else 5
            focused_items=self._select_top_items(scored_items, max_focus)
            
            # Determine current focus
            current_focus=self._determine_current_focus(focused_items)
            
            # Update state
            self._focus_items=focused_items
            self._current_focus=current_focus
            self._metrics["items_processed"]+=len(items)
            
            return AttentionResult(
                focused_items=focused_items,
                current_focus=current_focus,
                attention_weights=self._get_attention_weights(context)
            )
        except Exception as e:
            self._metrics["errors"]+=1
            raise AttentionError(f"Failed to focus attention: {e}") from e
    
    def _create_focus_items(self, data: Any, context: Optional[Dict[str, Any]]) -> List[FocusItem]:
        """Create focus items from input data."""
        items=[]
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                item_id=f"focus_{i}"
                if isinstance(item, dict):
                    content=item.get("content", item)
                    priority=self._infer_priority(item, context)
                else:
                    content=item
                    priority=PriorityLevel.NORMAL
                items.append(FocusItem(item_id=item_id, content=content, priority=priority))
        else:
            item_id="focus_0"
            priority=self._infer_priority(data, context) if isinstance(data, dict) else PriorityLevel.NORMAL
            items.append(FocusItem(item_id=item_id, content=data, priority=priority))
        
        return items
    
    def _infer_priority(self, item: Dict[str, Any], context: Optional[Dict[str, Any]]) -> PriorityLevel:
        """Infer priority level from item and context."""
        if context and context.get("urgent"): return PriorityLevel.CRITICAL
        if item.get("priority")=="critical": return PriorityLevel.CRITICAL
        if item.get("priority")=="high": return PriorityLevel.HIGH
        if item.get("priority")=="low": return PriorityLevel.LOW
        return PriorityLevel.NORMAL
    
    def _score_items(self, items: List[FocusItem], context: Optional[Dict[str, Any]]) -> List[FocusItem]:
        """Score focus items based on multiple factors."""
        scored_items=[]
        
        for item in items:
            # Calculate scores for each factor
            relevance=self._calculate_relevance(item, context)
            novelty=self._calculate_novelty(item, context)
            urgency=self._calculate_urgency(item, context)
            importance=self._calculate_importance(item, context)
            
            # Create scored item
            scored_item=FocusItem(
                item_id=item.item_id,
                content=item.content,
                priority=item.priority,
                relevance=relevance,
                novelty=novelty,
                urgency=urgency,
                importance=importance
            )
            scored_items.append(scored_item)
        
        return scored_items
    
    def _calculate_relevance(self, item: FocusItem, context: Optional[Dict[str, Any]]) -> float:
        """Calculate relevance score (0-1)."""
        # Base relevance from priority
        priority_score={
            PriorityLevel.CRITICAL: 1.0,
            PriorityLevel.HIGH: 0.8,
            PriorityLevel.NORMAL: 0.5,
            PriorityLevel.LOW: 0.2,
            PriorityLevel.BACKGROUND: 0.0
        }.get(item.priority, 0.5)
        
        # Boost based on context
        context_boost=0.0
        if context:
            if context.get("goal"):
                # Check if item relates to current goal
                content_str=str(item.content).lower()
                goal_str=str(context.get("goal")).lower()
                if goal_str in content_str:
                    context_boost=0.3
            if context.get("focus"):
                # Check if item relates to current focus
                focus_str=str(context.get("focus")).lower()
                content_str=str(item.content).lower()
                if focus_str in content_str:
                    context_boost=0.2
        
        return min(1.0, priority_score + context_boost)
    
    def _calculate_novelty(self, item: FocusItem, context: Optional[Dict[str, Any]]) -> float:
        """Calculate novelty score (0-1)."""
        # Check if we've seen this before (simplified)
        content_str=str(item.content)
        
        # In a real implementation, check against memory
        # For now, use a simple heuristic
        if len(content_str) < 10:
            return 0.1
        elif len(content_str) > 1000:
            return 0.3
        else:
            return 0.5
    
    def _calculate_urgency(self, item: FocusItem, context: Optional[Dict[str, Any]]) -> float:
        """Calculate urgency score (0-1)."""
        # Check for urgency indicators
        content_str=str(item.content).lower()
        
        urgency_indicators=["urgent", "immediate", "asap", "critical", "emergency", "now"]
        for indicator in urgency_indicators:
            if indicator in content_str:
                return 0.9
        
        # Check context for urgency
        if context and context.get("urgent"):
            return 0.8
        
        return 0.1
    
    def _calculate_importance(self, item: FocusItem, context: Optional[Dict[str, Any]]) -> float:
        """Calculate importance score (0-1)."""
        # Base importance from priority
        priority_score={
            PriorityLevel.CRITICAL: 1.0,
            PriorityLevel.HIGH: 0.8,
            PriorityLevel.NORMAL: 0.5,
            PriorityLevel.LOW: 0.2,
            PriorityLevel.BACKGROUND: 0.0
        }.get(item.priority, 0.5)
        
        # Boost based on content length (longer = more important)
        content_str=str(item.content)
        length_boost=min(0.3, len(content_str)/1000)
        
        return min(1.0, priority_score + length_boost)
    
    def _select_top_items(self, items: List[FocusItem], max_items: int) -> List[FocusItem]:
        """Select top items based on composite score."""
        # Calculate composite score for each item
        for item in items:
            # Weighted sum of all factors
            weights=self._get_attention_weights()
            item._composite_score=(
                weights.get("relevance", 0.4)*item.relevance +
                weights.get("novelty", 0.2)*item.novelty +
                weights.get("urgency", 0.2)*item.urgency +
                weights.get("importance", 0.2)*item.importance
            )
        
        # Sort by composite score
        sorted_items=sorted(items, key=lambda x: x._composite_score, reverse=True)
        
        # Return top items
        return sorted_items[:max_items]
    
    def _determine_current_focus(self, items: List[FocusItem]) -> Optional[FocusItem]:
        """Determine the current focus from focused items."""
        if not items:
            return None
        
        # Current focus is the highest scoring item
        return items[0]
    
    def _get_attention_weights(self, context: Optional[Dict[str, Any]]=None) -> Dict[str, float]:
        """Get attention weights from configuration or context."""
        if self._config and hasattr(self._config, 'attention'):
            return {
                "relevance": self._config.attention.priority_weights.get("goal_relevance", 0.4),
                "novelty": self._config.attention.priority_weights.get("novelty", 0.2),
                "urgency": self._config.attention.priority_weights.get("urgency", 0.2),
                "importance": self._config.attention.priority_weights.get("importance", 0.2),
            }
        return {"relevance": 0.4, "novelty": 0.2, "urgency": 0.2, "importance": 0.2}
    
    async def switch_focus(self, new_focus: FocusItem, reason: str="manual") -> None:
        """Switch focus to a new item."""
        if self._current_focus and self._current_focus.item_id==new_focus.item_id:
            return  # Already focused
        
        self._current_focus=new_focus
        self._metrics["focus_switches"]+=1
        logger.info(f"Focus switched to {new_focus.item_id} (reason: {reason})")
    
    def get_current_focus(self) -> Optional[FocusItem]:
        """Get the current focus."""
        return self._current_focus
    
    def get_focus_items(self) -> List[FocusItem]:
        """Get all current focus items."""
        return self._focus_items.copy()
    
    def clear_focus(self) -> None:
        """Clear all focus items."""
        self._focus_items=[]
        self._current_focus=None
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"AttentionEngine(initialized={self._initialized}, focus_items={len(self._focus_items)})"
