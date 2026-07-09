"""
Models for the AI Foundation Framework.
"""

from .base_model import AIModel, ModelCapabilities, ModelModality
from .chat_model import ChatModel
from .embedding_model import EmbeddingModel
from .vision_model import VisionModel
from .audio_model import AudioModel
from .structured_output_model import StructuredOutputModel

__all__ = [
    "AIModel",
    "ModelCapabilities",
    "ModelModality",
    "ChatModel",
    "EmbeddingModel",
    "VisionModel",
    "AudioModel",
    "StructuredOutputModel",
]
