"""
Streaming Manager for TangkuAgentOS AI Foundation Framework.

Manages streaming of AI model responses.
"""
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, field
import logging
import asyncio
from ..models.base_model import AIModel

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Represents a chunk of a streaming response."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamingResult:
    """Result of a streaming operation."""
    chunks: List[StreamChunk]
    model_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingManager:
    """Manages streaming of AI model responses for TangkuAgentOS.

    This class provides methods for streaming responses from AI models,
    including chunk collection, buffering, and error handling.
    """

    def __init__(self, model: AIModel):
        """Initialize the StreamingManager.

        Args:
            model: The AIModel to use for streaming.
        """
        self._model = model
        logger.info(f"StreamingManager initialized for model: {model.name}")

    async def stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a response from the AI model.

        Args:
            prompt: The prompt to stream.
            **kwargs: Additional arguments for the AI model.

        Yields:
            StreamChunk objects as they are generated.
        """
        try:
            async for chunk in self._model.stream_chat([{"role": "user", "content": prompt}], **kwargs):
                content = chunk.get("data", "")
                if content:
                    yield StreamChunk(
                        content=content,
                        metadata={"model": self._model.name},
                    )
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield StreamChunk(
                content=f"Error: {e}",
                metadata={"error": str(e)},
            )

    async def collect_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> StreamingResult:
        """Collect a full streaming response.

        Args:
            prompt: The prompt to stream.
            **kwargs: Additional arguments for the AI model.

        Returns:
            StreamingResult containing all chunks of the response.
        """
        chunks = []
        async for chunk in self.stream(prompt, **kwargs):
            chunks.append(chunk)
        return StreamingResult(
            chunks=chunks,
            model_name=self._model.name,
            metadata={"chunk_count": len(chunks)},
        )

    async def stream_with_buffer(
        self,
        prompt: str,
        buffer_size: int = 1,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a response with buffering.

        Args:
            prompt: The prompt to stream.
            buffer_size: Number of chunks to buffer before yielding.
            **kwargs: Additional arguments for the AI model.

        Yields:
            StreamChunk objects with buffered content.
        """
        buffer = []
        async for chunk in self.stream(prompt, **kwargs):
            buffer.append(chunk)
            if len(buffer) >= buffer_size:
                yield StreamChunk(
                    content="".join(c.content for c in buffer),
                    metadata={"buffered": True, "chunk_count": len(buffer)},
                )
                buffer.clear()
        if buffer:
            yield StreamChunk(
                content="".join(c.content for c in buffer),
                metadata={"buffered": True, "chunk_count": len(buffer)},
            )

    async def stream_to_callback(
        self,
        prompt: str,
        callback: callable,
        **kwargs: Any,
    ) -> None:
        """Stream a response to a callback function.

        Args:
            prompt: The prompt to stream.
            callback: Function to call for each chunk.
            **kwargs: Additional arguments for the AI model.
        """
        async for chunk in self.stream(prompt, **kwargs):
            callback(chunk)

    async def stream_with_timeout(
        self,
        prompt: str,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a response with a timeout.

        Args:
            prompt: The prompt to stream.
            timeout: Maximum time to stream in seconds.
            **kwargs: Additional arguments for the AI model.

        Yields:
            StreamChunk objects until the timeout is reached.
        """
        start_time = asyncio.get_event_loop().time()
        try:
            async for chunk in self.stream(prompt, **kwargs):
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout:
                    yield StreamChunk(
                        content="",
                        metadata={"timeout": True},
                    )
                    break
                yield chunk
        except asyncio.TimeoutError:
            yield StreamChunk(
                content="",
                metadata={"timeout": True},
            )
