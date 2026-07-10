"""
Multi-Model Orchestrator for TangkuAgentOS AI Foundation Framework.

Manages multiple AI models for orchestration, fallback, and voting.
"""
from typing import Any, Optional, Dict, List, AsyncIterator
from dataclasses import dataclass, field
import logging
from ..models.base_model import AIModel
from ..providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result of a multi-model orchestration."""
    primary_model: str
    fallback_models: List[str]
    responses: Dict[str, Any]
    consensus: Optional[Any] = None
    voting_scores: Optional[Dict[str, float]] = None


class MultiModelOrchestrator:
    """Orchestrates multiple AI models for TangkuAgentOS.

    This class provides methods for executing prompts using multiple models,
    including primary-fallback patterns, parallel execution, and voting.
    """

    def __init__(
        self,
        primary_model: AIModel,
        fallback_models: Optional[List[AIModel]] = None,
    ):
        """Initialize the MultiModelOrchestrator.

        Args:
            primary_model: The primary AI model to use.
            fallback_models: Optional list of fallback AI models.
        """
        self._primary_model = primary_model
        self._fallback_models = fallback_models or []
        self._providers: Dict[str, BaseProvider] = {}
        logger.info("MultiModelOrchestrator initialized.")

    def add_provider(self, provider: BaseProvider) -> None:
        """Add a provider to the orchestrator.

        Args:
            provider: The provider to add.
        """
        self._providers[provider.name] = provider
        logger.info(f"Added provider: {provider.name}")

    async def execute(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute a prompt using the primary model and fallbacks.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional arguments for the AI models.

        Returns:
            OrchestrationResult containing the responses and metadata.
        """
        responses = {}

        # Execute primary model
        try:
            primary_response = await self._primary_model.chat([{"role": "user", "content": prompt}])
            responses[self._primary_model.name] = primary_response
            logger.info(f"Primary model {self._primary_model.name} executed successfully.")
        except Exception as e:
            responses[self._primary_model.name] = {"error": str(e)}
            logger.error(f"Primary model {self._primary_model.name} failed: {e}")

        # Execute fallback models if primary fails
        if "error" in responses.get(self._primary_model.name, {}):
            for model in self._fallback_models:
                try:
                    fallback_response = await model.chat([{"role": "user", "content": prompt}])
                    responses[model.name] = fallback_response
                    logger.info(f"Fallback model {model.name} executed successfully.")
                except Exception as e:
                    responses[model.name] = {"error": str(e)}
                    logger.error(f"Fallback model {model.name} failed: {e}")

        return OrchestrationResult(
            primary_model=self._primary_model.name,
            fallback_models=[model.name for model in self._fallback_models],
            responses=responses,
        )

    async def vote(
        self,
        prompt: str,
        models: List[AIModel],
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute a prompt using multiple models and determine consensus.

        Args:
            prompt: The prompt to execute.
            models: List of AI models to use for voting.
            **kwargs: Additional arguments for the AI models.

        Returns:
            OrchestrationResult containing the responses, consensus, and voting scores.
        """
        responses = {}
        voting_scores = {}

        for model in models:
            try:
                response = await model.chat([{"role": "user", "content": prompt}])
                responses[model.name] = response
                # Simple voting: Score based on response length
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                voting_scores[model.name] = len(content) / 1000.0
                logger.info(f"Model {model.name} voted with score: {voting_scores[model.name]}")
            except Exception as e:
                responses[model.name] = {"error": str(e)}
                voting_scores[model.name] = 0.0
                logger.error(f"Model {model.name} failed: {e}")

        # Determine consensus (simple majority for now)
        consensus = max(voting_scores, key=voting_scores.get) if voting_scores else None

        return OrchestrationResult(
            primary_model=self._primary_model.name,
            fallback_models=[model.name for model in models],
            responses=responses,
            consensus=consensus,
            voting_scores=voting_scores,
        )

    async def parallel_execute(
        self,
        prompt: str,
        models: List[AIModel],
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute a prompt using multiple models in parallel.

        Args:
            prompt: The prompt to execute.
            models: List of AI models to use.
            **kwargs: Additional arguments for the AI models.

        Returns:
            OrchestrationResult containing the responses from all models.
        """
        import asyncio

        async def execute_model(model: AIModel) -> Dict[str, Any]:
            try:
                response = await model.chat([{"role": "user", "content": prompt}])
                return {model.name: response}
            except Exception as e:
                return {model.name: {"error": str(e)}}

        tasks = [execute_model(model) for model in models]
        results = await asyncio.gather(*tasks)

        responses = {}
        for result in results:
            responses.update(result)

        return OrchestrationResult(
            primary_model=self._primary_model.name,
            fallback_models=[model.name for model in models],
            responses=responses,
        )

    def add_fallback_model(self, model: AIModel) -> None:
        """Add a fallback model to the orchestrator.

        Args:
            model: The fallback model to add.
        """
        self._fallback_models.append(model)
        logger.info(f"Added fallback model: {model.name}")

    def remove_fallback_model(self, model_name: str) -> bool:
        """Remove a fallback model from the orchestrator.

        Args:
            model_name: The name of the model to remove.

        Returns:
            True if the model was removed, False otherwise.
        """
        for i, model in enumerate(self._fallback_models):
            if model.name == model_name:
                self._fallback_models.pop(i)
                logger.info(f"Removed fallback model: {model_name}")
                return True
        return False
