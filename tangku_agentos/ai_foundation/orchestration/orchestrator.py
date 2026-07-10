"""
AI Foundation Framework - Multi-Model Orchestrator

This module provides the MultiModelOrchestrator class for coordinating
multiple AI models.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.model import AIModel
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class OrchestrationStrategy(Enum):
    """Strategy for multi-model orchestration."""
    PRIMARY = auto()
    FALLBACK = auto()
    PARALLEL = auto()
    VOTING = auto()
    CONSENSUS = auto()
    LOAD_BALANCING = auto()
    COST_OPTIMIZED = auto()
    LATENCY_OPTIMIZED = auto()
    QUALITY_OPTIMIZED = auto()
    CUSTOM = auto()


class ModelSelectionStrategy(Enum):
    """Strategy for selecting models."""
    FIRST_AVAILABLE = auto()
    BEST_CAPABILITY = auto()
    LOWEST_COST = auto()
    LOWEST_LATENCY = auto()
    HIGHEST_QUALITY = auto()
    RANDOM = auto()
    ROUND_ROBIN = auto()
    CUSTOM = auto()


@dataclass
class OrchestrationResult:
    """
    Result from a multi-model orchestration.
    
    Attributes:
        request: The original request.
        responses: List of responses from different models.
        selected_response: The selected response.
        strategy: Orchestration strategy used.
        metrics: Metrics for the orchestration.
        timestamp: When the orchestration was performed.
    """

    request: "AIRequest"
    responses: List["AIResponse"] = field(default_factory=list)
    selected_response: Optional["AIResponse"] = None
    strategy: OrchestrationStrategy = OrchestrationStrategy.PRIMARY
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def count(self) -> int:
        """Get the number of responses."""
        return len(self.responses)

    @property
    def best_response(self) -> Optional["AIResponse"]:
        """Get the best response."""
        if not self.responses:
            return None
        return max(self.responses, key=lambda x: x.output_tokens if hasattr(x, 'output_tokens') else 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request": self.request.to_dict() if hasattr(self.request, 'to_dict') else str(self.request),
            "responses": [r.to_dict() for r in self.responses],
            "selected_response": self.selected_response.to_dict() if self.selected_response else None,
            "strategy": self.strategy.value,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "count": self.count,
        }


@dataclass
class MultiModelOrchestratorMetrics:
    """Metrics for the multi-model orchestrator."""
    orchestrations: int = 0
    models_used: int = 0
    responses_generated: int = 0
    selections: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "orchestrations": self.orchestrations,
            "models_used": self.models_used,
            "responses_generated": self.responses_generated,
            "selections": self.selections,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class MultiModelOrchestrator:
    """
    Orchestrator for coordinating multiple AI models.
    
    This class provides advanced capabilities for working with multiple
    AI models, including fallback mechanisms, parallel execution,
    voting, consensus building, and optimization strategies.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import MultiModelOrchestrator
        >>> 
        >>> # Create orchestrator
        >>> orchestrator = MultiModelOrchestrator()
        >>> 
        >>> # Orchestrate a request
        >>> result = await orchestrator.orchestrate(
        ...     request=request,
        ...     strategy=OrchestrationStrategy.FALLBACK
        ... )
        >>> 
        >>> # Get the best response
        >>> best = result.selected_response
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the multi-model orchestrator.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = MultiModelOrchestratorMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._round_robin_index = 0
        
        logger.info("MultiModelOrchestrator initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> MultiModelOrchestratorMetrics:
        """Get the orchestrator metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the orchestrator is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the orchestrator is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the multi-model orchestrator.
        """
        if self._initialized:
            logger.warning("MultiModelOrchestrator already initialized")
            return
        
        logger.info("Initializing MultiModelOrchestrator...")
        
        self._initialized = True
        logger.info("MultiModelOrchestrator initialized successfully")

    async def start(self) -> None:
        """
        Start the multi-model orchestrator.
        """
        if self._started:
            logger.warning("MultiModelOrchestrator already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting MultiModelOrchestrator...")
        
        self._started = True
        logger.info("MultiModelOrchestrator started successfully")

    async def stop(self) -> None:
        """
        Stop the multi-model orchestrator.
        """
        if not self._started:
            logger.warning("MultiModelOrchestrator not started")
            return
        
        logger.info("Stopping MultiModelOrchestrator...")
        
        self._started = False
        logger.info("MultiModelOrchestrator stopped successfully")

    async def orchestrate(
        self,
        request: "AIRequest",
        strategy: OrchestrationStrategy = OrchestrationStrategy.PRIMARY,
        selection_strategy: ModelSelectionStrategy = ModelSelectionStrategy.FIRST_AVAILABLE,
        max_models: int = 3,
        timeout: Optional[float] = None,
    ) -> OrchestrationResult:
        """
        Orchestrate a request across multiple models.
        
        Args:
            request: AIRequest to orchestrate.
            strategy: Orchestration strategy to use.
            selection_strategy: Strategy for selecting models.
            max_models: Maximum number of models to use.
            timeout: Optional timeout for the orchestration.
        
        Returns:
            OrchestrationResult with the orchestration results.
        """
        async with self._lock:
            self._metrics.orchestrations += 1
            
            try:
                # Select models based on strategy
                models = await self._select_models(request, selection_strategy, max_models)
                
                if not models:
                    raise ValueError("No models available for orchestration")
                
                # Execute based on orchestration strategy
                if strategy == OrchestrationStrategy.PRIMARY:
                    result = await self._execute_primary(request, models)
                elif strategy == OrchestrationStrategy.FALLBACK:
                    result = await self._execute_fallback(request, models)
                elif strategy == OrchestrationStrategy.PARALLEL:
                    result = await self._execute_parallel(request, models)
                elif strategy == OrchestrationStrategy.VOTING:
                    result = await self._execute_voting(request, models)
                elif strategy == OrchestrationStrategy.CONSENSUS:
                    result = await self._execute_consensus(request, models)
                elif strategy == OrchestrationStrategy.LOAD_BALANCING:
                    result = await self._execute_load_balancing(request, models)
                elif strategy == OrchestrationStrategy.COST_OPTIMIZED:
                    result = await self._execute_cost_optimized(request, models)
                elif strategy == OrchestrationStrategy.LATENCY_OPTIMIZED:
                    result = await self._execute_latency_optimized(request, models)
                elif strategy == OrchestrationStrategy.QUALITY_OPTIMIZED:
                    result = await self._execute_quality_optimized(request, models)
                else:
                    result = await self._execute_primary(request, models)
                
                # Update metrics
                self._metrics.models_used += len(models)
                self._metrics.responses_generated += result.count
                self._metrics.selections += 1
                
                return result
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Orchestration failed: {e}")
                raise

    async def _select_models(
        self,
        request: "AIRequest",
        strategy: ModelSelectionStrategy,
        max_models: int,
    ) -> List["AIModel"]:
        """Select models based on the selection strategy."""
        # Get all available models
        all_models = await self._foundation.providers.list_models()
        
        if not all_models:
            return []
        
        # Filter models that can handle the request
        capable_models = [
            model for model in all_models
            if model.can_handle(request)
        ]
        
        if not capable_models:
            return []
        
        # Select models based on strategy
        if strategy == ModelSelectionStrategy.FIRST_AVAILABLE:
            return capable_models[:max_models]
        elif strategy == ModelSelectionStrategy.BEST_CAPABILITY:
            return sorted(
                capable_models,
                key=lambda m: len(m.capabilities.modalities),
                reverse=True
            )[:max_models]
        elif strategy == ModelSelectionStrategy.LOWEST_COST:
            return sorted(
                capable_models,
                key=lambda m: m.pricing.input_price_per_token + m.pricing.output_price_per_token
            )[:max_models]
        elif strategy == ModelSelectionStrategy.LOWEST_LATENCY:
            # In a real implementation, this would use actual latency data
            return capable_models[:max_models]
        elif strategy == ModelSelectionStrategy.HIGHEST_QUALITY:
            # In a real implementation, this would use quality metrics
            return capable_models[:max_models]
        elif strategy == ModelSelectionStrategy.RANDOM:
            import random
            random.shuffle(capable_models)
            return capable_models[:max_models]
        elif strategy == ModelSelectionStrategy.ROUND_ROBIN:
            # Use round-robin selection
            start_index = self._round_robin_index % len(capable_models)
            selected = capable_models[start_index:start_index + max_models]
            if len(selected) < max_models:
                selected.extend(capable_models[:max_models - len(selected)])
            self._round_robin_index = (self._round_robin_index + 1) % len(capable_models)
            return selected
        else:
            return capable_models[:max_models]

    async def _execute_primary(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute using the primary model."""
        if not models:
            raise ValueError("No models available")
        
        # Use the first model
        primary_model = models[0]
        request.model = primary_model.model_id
        request.provider = primary_model.provider
        
        # Execute the request
        response = await self._foundation.execute(request)
        
        return OrchestrationResult(
            request=request,
            responses=[response],
            selected_response=response,
            strategy=OrchestrationStrategy.PRIMARY,
            metrics={"model": primary_model.model_id},
        )

    async def _execute_fallback(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute with fallback to other models if the primary fails."""
        responses = []
        selected_response = None
        
        for model in models:
            try:
                request.model = model.model_id
                request.provider = model.provider
                
                response = await self._foundation.execute(request)
                responses.append(response)
                
                # If successful, use this response
                if not response.has_error():
                    selected_response = response
                    break
                    
            except Exception as e:
                logger.warning(f"Model {model.model_id} failed: {e}")
                continue
        
        if not selected_response and responses:
            # Use the first response even if it has errors
            selected_response = responses[0]
        
        return OrchestrationResult(
            request=request,
            responses=responses,
            selected_response=selected_response,
            strategy=OrchestrationStrategy.FALLBACK,
            metrics={"models_tried": len(models), "successful_models": len(responses)},
        )

    async def _execute_parallel(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute the request on all models in parallel."""
        responses = []
        
        # Create tasks for all models
        tasks = []
        for model in models:
            req = AIRequest(
                messages=request.messages,
                prompt=request.prompt,
                model=model.model_id,
                provider=model.provider,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                # Copy other request properties
            )
            tasks.append(self._foundation.execute(req))
        
        # Execute all tasks in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_responses = [r for r in responses if not isinstance(r, Exception)]
        
        # Select the best response (first successful one)
        selected_response = None
        for response in valid_responses:
            if not response.has_error():
                selected_response = response
                break
        
        if not selected_response and valid_responses:
            selected_response = valid_responses[0]
        
        return OrchestrationResult(
            request=request,
            responses=valid_responses,
            selected_response=selected_response,
            strategy=OrchestrationStrategy.PARALLEL,
            metrics={"models_used": len(models), "valid_responses": len(valid_responses)},
        )

    async def _execute_voting(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute the request on multiple models and select by voting."""
        # First, get responses from all models
        result = await self._execute_parallel(request, models)
        
        if not result.responses:
            return result
        
        # For voting, we need to compare responses
        # In a real implementation, this would use a voting mechanism
        # For now, just select the longest response
        selected_response = max(
            result.responses,
            key=lambda x: len(x.content) if x.content else 0
        )
        
        result.selected_response = selected_response
        result.strategy = OrchestrationStrategy.VOTING
        result.metrics["voting_method"] = "length"
        
        return result

    async def _execute_consensus(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute the request on multiple models and build consensus."""
        # First, get responses from all models
        result = await self._execute_parallel(request, models)
        
        if not result.responses:
            return result
        
        # For consensus, we need to find common elements in responses
        # In a real implementation, this would use a consensus algorithm
        # For now, just select the first response
        selected_response = result.responses[0]
        
        result.selected_response = selected_response
        result.strategy = OrchestrationStrategy.CONSENSUS
        result.metrics["consensus_method"] = "first"
        
        return result

    async def _execute_load_balancing(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute using load balancing."""
        # In a real implementation, this would track model usage and select the least used
        # For now, just use round-robin
        selected_model = models[self._round_robin_index % len(models)]
        self._round_robin_index = (self._round_robin_index + 1) % len(models)
        
        request.model = selected_model.model_id
        request.provider = selected_model.provider
        
        response = await self._foundation.execute(request)
        
        return OrchestrationResult(
            request=request,
            responses=[response],
            selected_response=response,
            strategy=OrchestrationStrategy.LOAD_BALANCING,
            metrics={"selected_model": selected_model.model_id},
        )

    async def _execute_cost_optimized(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute using the lowest cost model."""
        # Select the model with the lowest cost
        selected_model = min(
            models,
            key=lambda m: m.pricing.input_price_per_token + m.pricing.output_price_per_token
        )
        
        request.model = selected_model.model_id
        request.provider = selected_model.provider
        
        response = await self._foundation.execute(request)
        
        return OrchestrationResult(
            request=request,
            responses=[response],
            selected_response=response,
            strategy=OrchestrationStrategy.COST_OPTIMIZED,
            metrics={"selected_model": selected_model.model_id, "cost": selected_model.pricing.calculate_cost(request.input_tokens, 0)},
        )

    async def _execute_latency_optimized(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute using the lowest latency model."""
        # In a real implementation, this would use actual latency data
        # For now, just use the first model
        selected_model = models[0]
        
        request.model = selected_model.model_id
        request.provider = selected_model.provider
        
        response = await self._foundation.execute(request)
        
        return OrchestrationResult(
            request=request,
            responses=[response],
            selected_response=response,
            strategy=OrchestrationStrategy.LATENCY_OPTIMIZED,
            metrics={"selected_model": selected_model.model_id},
        )

    async def _execute_quality_optimized(
        self,
        request: "AIRequest",
        models: List["AIModel"],
    ) -> OrchestrationResult:
        """Execute using the highest quality model."""
        # In a real implementation, this would use quality metrics
        # For now, just use the model with the most capabilities
        selected_model = max(
            models,
            key=lambda m: len(m.capabilities.modalities)
        )
        
        request.model = selected_model.model_id
        request.provider = selected_model.provider
        
        response = await self._foundation.execute(request)
        
        return OrchestrationResult(
            request=request,
            responses=[response],
            selected_response=response,
            strategy=OrchestrationStrategy.QUALITY_OPTIMIZED,
            metrics={"selected_model": selected_model.model_id, "capabilities": len(selected_model.capabilities.modalities)},
        )

    async def select_model(
        self,
        request: "AIRequest",
        strategy: ModelSelectionStrategy = ModelSelectionStrategy.FIRST_AVAILABLE,
    ) -> Optional["AIModel"]:
        """
        Select a single model for a request.
        
        Args:
            request: AIRequest to select a model for.
            strategy: Strategy for selecting the model.
        
        Returns:
            Selected AIModel or None if no model available.
        """
        models = await self._select_models(request, strategy, max_models=1)
        return models[0] if models else None

    async def compare_models(
        self,
        request: "AIRequest",
        model_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Compare multiple models on a request.
        
        Args:
            request: AIRequest to compare models on.
            model_ids: List of model IDs to compare.
        
        Returns:
            Dictionary with comparison results.
        """
        comparison = {
            "request": request.to_dict() if hasattr(request, 'to_dict') else str(request),
            "models": {},
        }
        
        for model_id in model_ids:
            try:
                model = await self._foundation.providers.get_model(model_id)
                if not model:
                    comparison["models"][model_id] = {"error": "Model not found"}
                    continue
                
                request.model = model_id
                request.provider = model.provider
                
                start_time = time.time()
                response = await self._foundation.execute(request)
                duration = time.time() - start_time
                
                comparison["models"][model_id] = {
                    "response": response.to_dict() if hasattr(response, 'to_dict') else str(response),
                    "duration": duration,
                    "tokens": response.total_tokens if hasattr(response, 'total_tokens') else 0,
                    "cost": model.calculate_cost(request, response) if hasattr(model, 'calculate_cost') else 0,
                }
                
            except Exception as e:
                comparison["models"][model_id] = {"error": str(e)}
        
        return comparison

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the multi-model orchestrator.
        
        Returns:
            Dictionary with orchestrator information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "default_strategy": OrchestrationStrategy.PRIMARY.value,
                "default_selection_strategy": ModelSelectionStrategy.FIRST_AVAILABLE.value,
            }
        }

    async def reset(self) -> None:
        """
        Reset the multi-model orchestrator.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting MultiModelOrchestrator...")
        
        self._metrics = MultiModelOrchestratorMetrics()
        self._initialized = False
        self._started = False
        self._round_robin_index = 0
        
        logger.info("MultiModelOrchestrator reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MultiModelOrchestrator("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"orchestrations={self._metrics.orchestrations})"
        )
