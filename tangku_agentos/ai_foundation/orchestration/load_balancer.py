"""
Load Balancer for TangkuAgentOS AI Foundation Framework.

Distributes requests across multiple AI models for optimal performance.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import asyncio
from collections import defaultdict
from ..models.base_model import AIModel

logger = logging.getLogger(__name__)


@dataclass
class LoadBalanceResult:
    """Result of a load balancing operation."""
    model_name: str
    response: Dict[str, Any]
    latency: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelStats:
    """Statistics for a model."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    current_load: int = 0


class LoadBalancer:
    """Distributes requests across multiple AI models for TangkuAgentOS.

    This class implements various load balancing strategies to optimize
    performance, cost, and reliability when using multiple AI models.
    """

    def __init__(
        self,
        models: List[AIModel],
        strategy: str = "round_robin",
    ):
        """Initialize the LoadBalancer.

        Args:
            models: List of AI models to balance load across.
            strategy: The load balancing strategy to use (e.g., "round_robin", "random", "least_load").
        """
        self._models = models
        self._strategy = strategy
        self._model_stats: Dict[str, ModelStats] = defaultdict(ModelStats)
        self._round_robin_index = 0
        logger.info(f"LoadBalancer initialized with strategy: {strategy}")

    async def balance(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> LoadBalanceResult:
        """Balance a request across available models.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional arguments for the AI models.

        Returns:
            LoadBalanceResult containing the model used and its response.
        """
        model = self._select_model()
        if not model:
            raise ValueError("No available models for load balancing.")

        start_time = asyncio.get_event_loop().time()
        try:
            response = await model.chat([{"role": "user", "content": prompt}])
            latency = asyncio.get_event_loop().time() - start_time
            self._update_stats(model.name, True, latency)
            logger.info(f"Model {model.name} processed request in {latency:.2f}s")
            return LoadBalanceResult(
                model_name=model.name,
                response=response,
                latency=latency,
                metadata={"strategy": self._strategy},
            )
        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            self._update_stats(model.name, False, latency)
            logger.error(f"Model {model.name} failed: {e}")
            return LoadBalanceResult(
                model_name=model.name,
                response={"error": str(e)},
                latency=latency,
                metadata={"error": str(e)},
            )

    def _select_model(self) -> Optional[AIModel]:
        """Select a model based on the current strategy.

        Returns:
            The selected AIModel, or None if no models are available.
        """
        if not self._models:
            return None

        if self._strategy == "round_robin":
            return self._round_robin_select()
        elif self._strategy == "random":
            return self._random_select()
        elif self._strategy == "least_load":
            return self._least_load_select()
        elif self._strategy == "weighted":
            return self._weighted_select()
        else:
            return self._round_robin_select()

    def _round_robin_select(self) -> AIModel:
        """Select a model using round-robin strategy."""
        model = self._models[self._round_robin_index % len(self._models)]
        self._round_robin_index += 1
        return model

    def _random_select(self) -> AIModel:
        """Select a model randomly."""
        import random
        return random.choice(self._models)

    def _least_load_select(self) -> AIModel:
        """Select the model with the least current load."""
        return min(
            self._models,
            key=lambda m: self._model_stats[m.name].current_load,
        )

    def _weighted_select(self) -> AIModel:
        """Select a model based on weighted performance."""
        # Simple weight: success rate * (1 / average latency)
        weighted_models = []
        for model in self._models:
            stats = self._model_stats[model.name]
            if stats.total_requests == 0:
                weight = 1.0
            else:
                success_rate = stats.successful_requests / stats.total_requests
                avg_latency = stats.total_latency / stats.total_requests if stats.total_requests > 0 else 1.0
                weight = success_rate / avg_latency if avg_latency > 0 else success_rate
            weighted_models.append((model, weight))
        weighted_models.sort(key=lambda x: x[1], reverse=True)
        return weighted_models[0][0] if weighted_models else self._models[0]

    def _update_stats(
        self,
        model_name: str,
        success: bool,
        latency: float,
    ) -> None:
        """Update statistics for a model.

        Args:
            model_name: The name of the model.
            success: Whether the request was successful.
            latency: The latency of the request in seconds.
        """
        stats = self._model_stats[model_name]
        stats.total_requests += 1
        stats.total_latency += latency
        if success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
        stats.current_load = stats.total_requests - (stats.successful_requests + stats.failed_requests)

    def set_strategy(self, strategy: str) -> None:
        """Set the load balancing strategy.

        Args:
            strategy: The strategy to use (e.g., "round_robin", "random", "least_load", "weighted").
        """
        self._strategy = strategy
        logger.info(f"Set load balancing strategy to: {strategy}")

    def get_stats(self) -> Dict[str, ModelStats]:
        """Get statistics for all models.

        Returns:
            Dictionary mapping model names to their statistics.
        """
        return dict(self._model_stats)

    def reset_stats(self) -> None:
        """Reset all model statistics."""
        self._model_stats.clear()
        self._round_robin_index = 0
        logger.info("Reset all model statistics.")
