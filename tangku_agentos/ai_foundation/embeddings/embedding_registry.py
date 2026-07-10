"""
Embedding Registry for TangkuAgentOS AI Foundation Framework.

Manages embedding models and their capabilities.
"""
from typing import Any, Optional, Dict, List, Type
from dataclasses import dataclass
import logging
from ..models.base_model import AIModel, EmbeddingModel

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCapabilities:
    """Capabilities of an embedding model."""
    dimension: int
    max_input_length: int
    batch_support: bool
    pricing: Dict[str, float]


class EmbeddingRegistry:
    """Manages embedding models for TangkuAgentOS.

    This class provides a registry for embedding models, allowing
    dynamic registration and retrieval of models by name.
    """

    def __init__(self):
        """Initialize the EmbeddingRegistry."""
        self._embedding_models: Dict[str, EmbeddingModel] = {}
        logger.info("EmbeddingRegistry initialized.")

    def register_model(
        self,
        model_name: str,
        model: EmbeddingModel,
    ) -> None:
        """Register an embedding model.

        Args:
            model_name: The name of the model to register.
            model: The embedding model instance.
        """
        self._embedding_models[model_name] = model
        logger.info(f"Registered embedding model: {model_name}")

    def get_model(self, model_name: str) -> Optional[EmbeddingModel]:
        """Retrieve an embedding model by name.

        Args:
            model_name: The name of the model to retrieve.

        Returns:
            The embedding model if found, otherwise None.
        """
        return self._embedding_models.get(model_name)

    def list_models(self) -> List[str]:
        """List all registered embedding models.

        Returns:
            List of model names.
        """
        return list(self._embedding_models.keys())

    async def embed(
        self,
        text: str,
        model_name: str = "default",
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings for text using a registered model.

        Args:
            text: The text to embed.
            model_name: The name of the model to use.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            The embedding vector.

        Raises:
            ValueError: If the specified model is not found.
        """
        model = self._embedding_models.get(model_name)
        if not model:
            raise ValueError(f"Embedding model '{model_name}' not found.")
        return await model.embed(text, **kwargs)

    async def embed_batch(
        self,
        texts: List[str],
        model_name: str = "default",
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts using a registered model.

        Args:
            texts: The list of texts to embed.
            model_name: The name of the model to use.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            List of embedding vectors.

        Raises:
            ValueError: If the specified model is not found.
        """
        model = self._embedding_models.get(model_name)
        if not model:
            raise ValueError(f"Embedding model '{model_name}' not found.")
        return await model.embed_batch(texts, **kwargs)

    def unregister_model(self, model_name: str) -> bool:
        """Unregister an embedding model.

        Args:
            model_name: The name of the model to unregister.

        Returns:
            True if the model was unregistered, False otherwise.
        """
        if model_name in self._embedding_models:
            del self._embedding_models[model_name]
            logger.info(f"Unregistered embedding model: {model_name}")
            return True
        return False
