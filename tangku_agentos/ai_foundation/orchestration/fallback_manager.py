"""
Fallback Manager for TangkuAgentOS AI Foundation Framework.

Manages fallback logic for AI model execution.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
from ..models.base_model import AIModel

logger = logging.getLogger(__name__)


@dataclass
class FallbackResult:
    """Result of a fallback operation."""
    primary_model: str
    fallback_model: Optional[str]
    primary_response: Optional[Dict[str, Any]]
    fallback_response: Optional[Dict[str, Any]]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FallbackManager:
    """Manages fallback logic for AI model execution in TangkuAgentOS.

    This class provides methods for executing prompts with fallback models
    when the primary model fails or returns invalid results.
    """

    def __init__(
        self,
        primary_model: AIModel,
        fallback_models: Optional[List[AIModel]] = None,
    ):
        """Initialize the FallbackManager.

        Args:
            primary_model: The primary AI model to use.
            fallback_models: Optional list of fallback AI models.
        """
        self._primary_model = primary_model
        self._fallback_models = fallback_models or []
        logger.info("FallbackManager initialized.")

    async def execute_with_fallback(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> FallbackResult:
        """Execute a prompt with fallback models.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional arguments for the AI models.

        Returns:
            FallbackResult containing the primary and fallback responses.
        """
        # Try primary model
        try:
            primary_response = await self._primary_model.chat([{"role": "user", "content": prompt}])
            if self._is_valid_response(primary_response):
                logger.info(f"Primary model {self._primary_model.name} succeeded.")
                return FallbackResult(
                    primary_model=self._primary_model.name,
                    fallback_model=None,
                    primary_response=primary_response,
                    fallback_response=None,
                    metadata={"status": "primary_success"},
                )
        except Exception as e:
            logger.warning(f"Primary model {self._primary_model.name} failed: {e}")

        # Try fallback models in order
        for fallback_model in self._fallback_models:
            try:
                fallback_response = await fallback_model.chat([{"role": "user", "content": prompt}])
                if self._is_valid_response(fallback_response):
                    logger.info(f"Fallback model {fallback_model.name} succeeded.")
                    return FallbackResult(
                        primary_model=self._primary_model.name,
                        fallback_model=fallback_model.name,
                        primary_response={"error": str(e)},
                        fallback_response=fallback_response,
                        metadata={"status": "fallback_success"},
                    )
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model.name} failed: {e}")

        return FallbackResult(
            primary_model=self._primary_model.name,
            fallback_model=None,
            primary_response={"error": "Primary model failed"},
            fallback_response={"error": "All fallback models failed"},
            error="All models failed",
            metadata={"status": "all_failed"},
        )

    def _is_valid_response(self, response: Dict[str, Any]) -> bool:
        """Check if a response is valid.

        Args:
            response: The response to validate.

        Returns:
            True if the response is valid, False otherwise.
        """
        if not response:
            return False
        if "error" in response:
            return False
        choices = response.get("choices", [])
        if not choices:
            return False
        return True

    def add_fallback_model(self, model: AIModel) -> None:
        """Add a fallback model to the manager.

        Args:
            model: The fallback model to add.
        """
        self._fallback_models.append(model)
        logger.info(f"Added fallback model: {model.name}")

    def remove_fallback_model(self, model_name: str) -> bool:
        """Remove a fallback model from the manager.

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

    def set_fallback_order(self, model_names: List[str]) -> None:
        """Set the order of fallback models.

        Args:
            model_names: List of model names in the desired order.
        """
        # Create a mapping from name to model
        model_map = {model.name: model for model in self._fallback_models}
        # Reorder based on the provided list
        self._fallback_models = [model_map[name] for name in model_names if name in model_map]
        logger.info(f"Set fallback order: {[model.name for model in self._fallback_models]}")
