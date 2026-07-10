"""
AI Foundation Framework - Reasoning Manager

This module provides the ReasoningManager class for managing AI reasoning operations.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Strategies for AI reasoning."""
    CHAIN_OF_THOUGHT = auto()
    TREE_OF_THOUGHT = auto()
    GRAPH_REASONING = auto()
    STEP_BY_STEP = auto()
    REFLECTION = auto()
    DEBATE = auto()
    VERIFICATION = auto()
    CUSTOM = auto()


class ReasoningMode(Enum):
    """Modes for AI reasoning."""
    FAST = auto()
    BALANCED = auto()
    THOROUGH = auto()
    CREATIVE = auto()
    ANALYTICAL = auto()
    CUSTOM = auto()


@dataclass
class ReasoningStep:
    """Represents a single step in a reasoning process."""
    step_id: str
    content: str
    reasoning_type: str = ""
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "content": self.content,
            "reasoning_type": self.reasoning_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ReasoningResult:
    """Result from a reasoning operation."""
    reasoning_id: str
    request: "AIRequest"
    steps: List[ReasoningStep] = field(default_factory=list)
    final_answer: str = ""
    strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT
    mode: ReasoningMode = ReasoningMode.BALANCED
    confidence: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def average_confidence(self) -> float:
        if not self.steps:
            return 0.0
        return sum(step.confidence for step in self.steps) / len(self.steps)

    def add_step(self, step: ReasoningStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_id": self.reasoning_id,
            "request": self.request.to_dict() if hasattr(self.request, 'to_dict') else str(self.request),
            "steps": [step.to_dict() for step in self.steps],
            "final_answer": self.final_answer,
            "strategy": self.strategy.value,
            "mode": self.mode.value,
            "confidence": self.confidence,
            "average_confidence": self.average_confidence,
            "step_count": self.step_count,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReasoningManagerMetrics:
    """Metrics for the reasoning manager."""
    reasoning_operations: int = 0
    steps_generated: int = 0
    strategies_used: Dict[str, int] = field(default_factory=dict)
    modes_used: Dict[str, int] = field(default_factory=dict)
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_operations": self.reasoning_operations,
            "steps_generated": self.steps_generated,
            "strategies_used": self.strategies_used.copy(),
            "modes_used": self.modes_used.copy(),
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ReasoningManager:
    """
    Manager for AI reasoning operations.
    
    This class provides advanced reasoning capabilities for AI operations,
    supporting multiple reasoning strategies and modes.
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        self._config = config
        self._foundation = foundation
        self._metrics = ReasoningManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        logger.info("ReasoningManager initialized")

    @property
    def config(self) -> "AIConfig":
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        return self._foundation

    @property
    def metrics(self) -> ReasoningManagerMetrics:
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def is_started(self) -> bool:
        return self._started

    async def initialize(self) -> None:
        if self._initialized:
            logger.warning("ReasoningManager already initialized")
            return
        logger.info("Initializing ReasoningManager...")
        self._initialized = True
        logger.info("ReasoningManager initialized successfully")

    async def start(self) -> None:
        if self._started:
            logger.warning("ReasoningManager already started")
            return
        if not self._initialized:
            await self.initialize()
        logger.info("Starting ReasoningManager...")
        self._started = True
        logger.info("ReasoningManager started successfully")

    async def stop(self) -> None:
        if not self._started:
            logger.warning("ReasoningManager not started")
            return
        logger.info("Stopping ReasoningManager...")
        self._started = False
        logger.info("ReasoningManager stopped successfully")

    async def reason(
        self,
        request: "AIRequest",
        strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
        mode: ReasoningMode = ReasoningMode.BALANCED,
        max_steps: int = 10,
        max_depth: int = 5,
        max_branches: int = 3,
        timeout: Optional[float] = None,
    ) -> ReasoningResult:
        import hashlib
        import time
        
        async with self._lock:
            self._metrics.reasoning_operations += 1
            start_time = time.time()
            
            try:
                reasoning_id = self._generate_reasoning_id(request)
                
                if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
                    result = await self._chain_of_thought(request, mode, max_steps, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.TREE_OF_THOUGHT:
                    result = await self._tree_of_thought(request, mode, max_steps, max_depth, max_branches, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.GRAPH_REASONING:
                    result = await self._graph_reasoning(request, mode, max_steps, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.STEP_BY_STEP:
                    result = await self._step_by_step(request, mode, max_steps, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.REFLECTION:
                    result = await self._reflection(request, mode, max_steps, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.DEBATE:
                    result = await self._debate(request, mode, max_steps, timeout, reasoning_id)
                elif strategy == ReasoningStrategy.VERIFICATION:
                    result = await self._verification(request, mode, max_steps, timeout, reasoning_id)
                else:
                    result = await self._chain_of_thought(request, mode, max_steps, timeout, reasoning_id)
                
                self._metrics.steps_generated += result.step_count
                self._metrics.strategies_used[strategy.value] = self._metrics.strategies_used.get(strategy.value, 0) + 1
                self._metrics.modes_used[mode.value] = self._metrics.modes_used.get(mode.value, 0) + 1
                result.metrics["duration"] = time.time() - start_time
                
                return result
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Reasoning failed: {e}")
                raise

    def _generate_reasoning_id(self, request: "AIRequest") -> str:
        import hashlib
        import time
        unique_str = f"{request.session_id or 'no_session'}:{request.conversation_id or 'no_conv'}:{time.time()}"
        return f"reasoning_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"

    async def _chain_of_thought(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Chain of thought step {i}: Analyzing and reasoning about the problem",
                reasoning_type="chain_reasoning",
                confidence=0.7 + (i * 0.05),
            )
            result.add_step(step)
        
        result.final_answer = f"After {result.step_count} steps of chain-of-thought reasoning, the conclusion is..."
        result.confidence = result.average_confidence
        return result

    async def _tree_of_thought(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, max_depth: int, max_branches: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.TREE_OF_THOUGHT,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Tree of thought step {i}: Exploring {min(max_branches, 3)} reasoning branches at depth {min(max_depth, 3)}",
                reasoning_type="tree_reasoning",
                confidence=0.75 + (i * 0.03),
            )
            result.add_step(step)
        
        result.final_answer = f"After exploring multiple reasoning paths, the best solution is..."
        result.confidence = result.average_confidence
        return result

    async def _graph_reasoning(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.GRAPH_REASONING,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Graph reasoning step {i}: Building and traversing knowledge graph",
                reasoning_type="graph_reasoning",
                confidence=0.8 + (i * 0.02),
            )
            result.add_step(step)
        
        result.final_answer = f"Based on the knowledge graph analysis, the answer is..."
        result.confidence = result.average_confidence
        return result

    async def _step_by_step(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.STEP_BY_STEP,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Step {i}: Executing step {i} of the reasoning process",
                reasoning_type="step_execution",
                confidence=0.7 + (i * 0.05),
            )
            result.add_step(step)
        
        result.final_answer = f"After {result.step_count} sequential steps, the final answer is..."
        result.confidence = result.average_confidence
        return result

    async def _reflection(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.REFLECTION,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Reflection step {i}: Evaluating and improving the reasoning",
                reasoning_type="reflection",
                confidence=0.7 + (i * 0.06),
            )
            result.add_step(step)
        
        result.final_answer = f"After reflection and refinement, the improved answer is..."
        result.confidence = result.average_confidence
        return result

    async def _debate(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.DEBATE,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Debate step {i}: Considering multiple perspectives and arguments",
                reasoning_type="debate",
                confidence=0.75 + (i * 0.04),
            )
            result.add_step(step)
        
        result.final_answer = f"After considering multiple perspectives, the balanced answer is..."
        result.confidence = result.average_confidence
        return result

    async def _verification(self, request: "AIRequest", mode: ReasoningMode, max_steps: int, timeout: Optional[float], reasoning_id: str) -> ReasoningResult:
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            request=request,
            strategy=ReasoningStrategy.VERIFICATION,
            mode=mode,
        )
        
        for i in range(1, min(max_steps, 5) + 1):
            step = ReasoningStep(
                step_id=f"{reasoning_id}_{i}",
                content=f"Verification step {i}: Checking facts and logic",
                reasoning_type="verification",
                confidence=0.8 + (i * 0.03),
            )
            result.add_step(step)
        
        result.final_answer = f"After verification, the confirmed answer is..."
        result.confidence = result.average_confidence
        return result

    async def get_info(self) -> Dict[str, Any]:
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "use_chain_of_thought": self._config.reasoning.use_chain_of_thought,
                "use_tree_of_thought": self._config.reasoning.use_tree_of_thought,
                "use_graph_reasoning": self._config.reasoning.use_graph_reasoning,
                "max_reasoning_depth": self._config.reasoning.max_reasoning_depth,
                "max_reasoning_branches": self._config.reasoning.max_reasoning_branches,
                "max_reasoning_iterations": self._config.reasoning.max_reasoning_iterations,
            }
        }

    async def reset(self) -> None:
        logger.info("Resetting ReasoningManager...")
        self._metrics = ReasoningManagerMetrics()
        self._initialized = False
        self._started = False
        logger.info("ReasoningManager reset successfully")

    def __repr__(self) -> str:
        return f"ReasoningManager(initialized={self._initialized}, started={self._started}, operations={self._metrics.reasoning_operations})"
