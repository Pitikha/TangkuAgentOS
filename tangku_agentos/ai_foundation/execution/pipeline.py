"""
AI Foundation Framework - Execution Pipeline

This module provides the ExecutionPipeline class for executing AI requests.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse, StreamChunk
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class ExecutionStep(Enum):
    """Steps in the execution pipeline."""
    VALIDATE = auto()
    ASSEMBLE_CONTEXT = auto()
    RETRIEVE_MEMORY = auto()
    RETRIEVE_KNOWLEDGE = auto()
    SELECT_MODEL = auto()
    BUILD_PROMPT = auto()
    ESTIMATE_TOKENS = auto()
    EXECUTE_MODEL = auto()
    VALIDATE_OUTPUT = auto()
    EXECUTE_TOOLS = auto()
    UPDATE_MEMORY = auto()
    RETURN_RESULT = auto()


class ExecutionStatus(Enum):
    """Status of an execution."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    CANCELLED = auto()


@dataclass
class ExecutionPipelineMetrics:
    """Metrics for the execution pipeline."""
    executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    tokens_processed: int = 0
    cost_incurred: float = 0.0
    latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    tool_executions: int = 0
    memory_retrievals: int = 0
    knowledge_retrievals: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "executions": self.executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "tokens_processed": self.tokens_processed,
            "cost_incurred": self.cost_incurred,
            "latency_ms": self.latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "tool_executions": self.tool_executions,
            "memory_retrievals": self.memory_retrievals,
            "knowledge_retrievals": self.knowledge_retrievals,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ExecutionPipeline:
    """
    Pipeline for executing AI requests.
    
    This class implements the complete AI execution pipeline that processes
    requests through multiple stages including validation, context assembly,
    memory retrieval, model execution, and result processing.
    
    The pipeline follows these steps:
    1. VALIDATE: Validate the request
    2. ASSEMBLE_CONTEXT: Assemble context from various sources
    3. RETRIEVE_MEMORY: Retrieve relevant memories
    4. RETRIEVE_KNOWLEDGE: Retrieve relevant knowledge
    5. SELECT_MODEL: Select the appropriate model
    6. BUILD_PROMPT: Build the prompt for the model
    7. ESTIMATE_TOKENS: Estimate token usage
    8. EXECUTE_MODEL: Execute the model
    9. VALIDATE_OUTPUT: Validate the model output
    10. EXECUTE_TOOLS: Execute any tool calls
    11. UPDATE_MEMORY: Update memory with new information
    12. RETURN_RESULT: Return the final result
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ExecutionPipeline
        >>> 
        >>> # Create pipeline
        >>> pipeline = ExecutionPipeline()
        >>> 
        >>> # Execute a request
        >>> response = await pipeline.execute(request)
        >>> 
        >>> # Execute with streaming
        >>> async for chunk in pipeline.execute_stream(request):
        ...     print(chunk.content)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the execution pipeline.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = ExecutionPipelineMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ExecutionPipeline initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> ExecutionPipelineMetrics:
        """Get the execution pipeline metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the pipeline is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the pipeline is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the execution pipeline.
        """
        if self._initialized:
            logger.warning("ExecutionPipeline already initialized")
            return
        
        logger.info("Initializing ExecutionPipeline...")
        
        self._initialized = True
        logger.info("ExecutionPipeline initialized successfully")

    async def start(self) -> None:
        """
        Start the execution pipeline.
        """
        if self._started:
            logger.warning("ExecutionPipeline already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ExecutionPipeline...")
        
        self._started = True
        logger.info("ExecutionPipeline started successfully")

    async def stop(self) -> None:
        """
        Stop the execution pipeline.
        """
        if not self._started:
            logger.warning("ExecutionPipeline not started")
            return
        
        logger.info("Stopping ExecutionPipeline...")
        
        self._started = False
        logger.info("ExecutionPipeline stopped successfully")

    async def execute(self, request: "AIRequest") -> "AIResponse":
        """
        Execute an AI request through the pipeline.
        
        Args:
            request: AIRequest to execute.
        
        Returns:
            AIResponse with the execution result.
        
        Raises:
            Exception: If execution fails.
        """
        start_time = time.time()
        
        async with self._lock:
            self._metrics.executions += 1
            
            try:
                # Create execution context
                context = {
                    "request": request,
                    "start_time": start_time,
                    "steps": [],
                    "errors": [],
                    "warnings": [],
                    "metrics": {},
                }
                
                # Execute each step
                for step in ExecutionStep:
                    try:
                        result = await self._execute_step(step, request, context)
                        context["steps"].append({"step": step.name, "result": result})
                    except Exception as e:
                        context["errors"].append({"step": step.name, "error": str(e)})
                        logger.error(f"Step {step.name} failed: {e}")
                        # Continue to next step if possible
                
                # Build final response
                response = await self._build_response(request, context)
                
                # Update metrics
                duration = time.time() - start_time
                self._metrics.latency_ms += duration * 1000
                self._metrics.successful_executions += 1
                
                return response
                
            except Exception as e:
                self._metrics.failed_executions += 1
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                
                # Build error response
                return self._build_error_response(request, str(e))

    async def execute_stream(self, request: "AIRequest") -> AsyncGenerator["StreamChunk", None]:
        """
        Execute an AI request with streaming.
        
        Args:
            request: AIRequest to execute.
        
        Yields:
            StreamChunk with parts of the response.
        
        Raises:
            Exception: If execution fails.
        """
        start_time = time.time()
        
        async with self._lock:
            self._metrics.executions += 1
            
            try:
                # Execute steps up to model execution
                context = {
                    "request": request,
                    "start_time": start_time,
                    "steps": [],
                    "errors": [],
                    "warnings": [],
                    "metrics": {},
                }
                
                # Execute steps before model execution
                for step in ExecutionStep:
                    if step == ExecutionStep.EXECUTE_MODEL:
                        break
                    try:
                        result = await self._execute_step(step, request, context)
                        context["steps"].append({"step": step.name, "result": result})
                    except Exception as e:
                        context["errors"].append({"step": step.name, "error": str(e)})
                        logger.error(f"Step {step.name} failed: {e}")
                        raise
                
                # Execute model with streaming
                async for chunk in self._execute_model_stream(request, context):
                    yield chunk
                
                # Update metrics
                duration = time.time() - start_time
                self._metrics.latency_ms += duration * 1000
                self._metrics.successful_executions += 1
                
            except Exception as e:
                self._metrics.failed_executions += 1
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                
                # Yield error chunk
                yield StreamChunk(
                    id=f"error_{int(time.time() * 1000)}",
                    content=f"Error: {str(e)}",
                    role="assistant",
                    finish_reason=None,
                    error=str(e),
                )

    async def _execute_step(
        self,
        step: ExecutionStep,
        request: "AIRequest",
        context: Dict[str, Any],
    ) -> Any:
        """
        Execute a single step in the pipeline.
        
        Args:
            step: Step to execute.
            request: AIRequest being processed.
            context: Execution context.
        
        Returns:
            Result of the step execution.
        """
        if step == ExecutionStep.VALIDATE:
            return await self._validate_request(request)
        elif step == ExecutionStep.ASSEMBLE_CONTEXT:
            return await self._assemble_context(request, context)
        elif step == ExecutionStep.RETRIEVE_MEMORY:
            return await self._retrieve_memory(request, context)
        elif step == ExecutionStep.RETRIEVE_KNOWLEDGE:
            return await self._retrieve_knowledge(request, context)
        elif step == ExecutionStep.SELECT_MODEL:
            return await self._select_model(request, context)
        elif step == ExecutionStep.BUILD_PROMPT:
            return await self._build_prompt(request, context)
        elif step == ExecutionStep.ESTIMATE_TOKENS:
            return await self._estimate_tokens(request, context)
        elif step == ExecutionStep.EXECUTE_MODEL:
            return await self._execute_model(request, context)
        elif step == ExecutionStep.VALIDATE_OUTPUT:
            return await self._validate_output(request, context)
        elif step == ExecutionStep.EXECUTE_TOOLS:
            return await self._execute_tools(request, context)
        elif step == ExecutionStep.UPDATE_MEMORY:
            return await self._update_memory(request, context)
        elif step == ExecutionStep.RETURN_RESULT:
            return await self._return_result(request, context)
        else:
            return None

    async def _validate_request(self, request: "AIRequest") -> bool:
        """Validate the AI request."""
        # Check required fields
        if not request.messages and not request.prompt:
            raise ValueError("Request must have messages or prompt")
        
        # Check token limits
        if request.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        # Check temperature
        if not (0.0 <= request.temperature <= 2.0):
            raise ValueError("temperature must be between 0 and 2")
        
        return True

    async def _assemble_context(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble context for the request."""
        # Use ContextAssembler to build context
        ai_context = await self._foundation.context.assemble(
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            request=request.to_dict(),
            context=request.context,
        )
        
        # Store context in execution context
        context["ai_context"] = ai_context
        
        return ai_context.to_dict()

    async def _retrieve_memory(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant memories."""
        if not request.use_memory or not self._config.memory.enabled:
            return {}
        
        self._metrics.memory_retrievals += 1
        
        # Use MemoryConnector to retrieve memories
        query = request.prompt or request.messages[-1].content if request.messages else ""
        memory_result = await self._foundation.memory.retrieve(
            query=query,
            limit=self._config.memory.max_memory_results,
        )
        
        # Store memory results in context
        context["memory_results"] = memory_result
        
        return memory_result.to_dict()

    async def _retrieve_knowledge(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant knowledge."""
        if not request.use_knowledge or not self._config.knowledge.enabled:
            return {}
        
        self._metrics.knowledge_retrievals += 1
        
        # Use KnowledgeConnector to retrieve knowledge
        query = request.prompt or request.messages[-1].content if request.messages else ""
        knowledge_result = await self._foundation.knowledge.retrieve(
            query=query,
            limit=self._config.knowledge.max_knowledge_results,
        )
        
        # Store knowledge results in context
        context["knowledge_results"] = knowledge_result
        
        return knowledge_result.to_dict()

    async def _select_model(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Select the appropriate model for the request."""
        # Use ProviderRegistry to route the request
        provider, model = await self._foundation.providers.route_request(request)
        
        if not provider or not model:
            # Use default model
            provider = self._foundation.providers.get_provider(
                self._config.providers.default_provider
            )
            if provider:
                model = provider.models[0] if provider.models else None
        
        if not model:
            raise ValueError("No model available for this request")
        
        # Store selected model in context
        context["selected_provider"] = provider
        context["selected_model"] = model
        
        return {
            "provider": provider.name if provider else None,
            "model": model.model_id if model else None,
        }

    async def _build_prompt(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Build the prompt for the model."""
        # Use PromptManager to build the prompt
        if request.messages:
            # For chat models, use the messages directly
            prompt = [msg.to_dict() for msg in request.messages]
        else:
            # For completion models, use the prompt
            prompt = request.prompt
        
        # Store prompt in context
        context["prompt"] = prompt
        
        return {"prompt": prompt}

    async def _estimate_tokens(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate token usage."""
        # Calculate input tokens
        input_tokens = request.input_tokens
        
        # Estimate output tokens (rough estimate based on max_tokens)
        output_tokens = min(request.max_tokens, self._config.models.max_output_tokens)
        
        # Calculate cost
        model = context.get("selected_model")
        if model:
            cost = model.calculate_cost(input_tokens, output_tokens)
        else:
            cost = 0.0
        
        # Store token estimate in context
        context["token_estimate"] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
        }
        
        # Update metrics
        self._metrics.tokens_processed += input_tokens + output_tokens
        self._metrics.cost_incurred += cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
        }

    async def _execute_model(self, request: "AIRequest", context: Dict[str, Any]) -> "AIResponse":
        """Execute the model."""
        provider = context.get("selected_provider")
        model = context.get("selected_model")
        prompt = context.get("prompt")
        
        if not provider or not model:
            raise ValueError("No provider or model selected")
        
        # Check if we should use cache
        if request.use_cache and self._config.cache.enabled:
            cache_key = self._generate_cache_key(request, context)
            cached_response = await self._foundation.cache.get(cache_key)
            if cached_response:
                self._metrics.cache_hits += 1
                return cached_response
            self._metrics.cache_misses += 1
        
        # Execute the model through the provider
        try:
            if request.stream:
                # For streaming, we need to collect all chunks
                chunks = []
                async for chunk in provider.chat_stream(request):
                    chunks.append(chunk)
                
                # Combine chunks into a single response
                response = self._combine_chunks(chunks)
            else:
                response = await provider.chat(request)
            
            # Cache the response if enabled
            if request.use_cache and self._config.cache.enabled:
                await self._foundation.cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            # Try fallback models if available
            if self._config.models.fallback_models:
                fallback_models = self._config.models.fallback_models.get(
                    model.model_id, []
                )
                for fallback_model_id in fallback_models:
                    try:
                        fallback_model = await provider.get_model(fallback_model_id)
                        if fallback_model:
                            request.model = fallback_model_id
                            if request.stream:
                                chunks = []
                                async for chunk in provider.chat_stream(request):
                                    chunks.append(chunk)
                                return self._combine_chunks(chunks)
                            else:
                                return await provider.chat(request)
                    except Exception:
                        continue
            
            raise

    async def _execute_model_stream(self, request: "AIRequest", context: Dict[str, Any]) -> AsyncGenerator["StreamChunk", None]:
        """Execute the model with streaming."""
        provider = context.get("selected_provider")
        model = context.get("selected_model")
        
        if not provider or not model:
            raise ValueError("No provider or model selected")
        
        # Execute the model with streaming
        try:
            async for chunk in provider.chat_stream(request):
                yield chunk
        except Exception as e:
            # Try fallback models if available
            if self._config.models.fallback_models:
                fallback_models = self._config.models.fallback_models.get(
                    model.model_id, []
                )
                for fallback_model_id in fallback_models:
                    try:
                        fallback_model = await provider.get_model(fallback_model_id)
                        if fallback_model:
                            request.model = fallback_model_id
                            async for chunk in provider.chat_stream(request):
                                yield chunk
                            return
                    except Exception:
                        continue
            
            raise

    def _combine_chunks(self, chunks: List["StreamChunk"]) -> "AIResponse":
        """Combine stream chunks into a single response."""
        from tangku_agentos.ai_foundation.models.response import AIResponse, Usage, FinishReason
        
        # Combine content
        content = "".join(chunk.content for chunk in chunks)
        
        # Calculate usage
        input_tokens = chunks[0].usage.input_tokens if chunks and chunks[0].usage else 0
        output_tokens = sum(chunk.usage.output_tokens if chunk.usage else 0 for chunk in chunks)
        
        # Get finish reason from last chunk
        finish_reason = chunks[-1].finish_reason if chunks else None
        
        return AIResponse(
            id=chunks[0].id if chunks else "",
            content=content,
            role="assistant",
            model=chunks[0].model if chunks else None,
            provider=None,
            finish_reason=finish_reason,
            usage=Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )

    async def _validate_output(self, request: "AIRequest", context: Dict[str, Any]) -> bool:
        """Validate the model output."""
        response = context.get("response")
        if not response:
            return False
        
        # Check for content
        if not response.content and not response.tool_calls:
            return False
        
        # Check for errors
        if response.has_error():
            return False
        
        return True

    async def _execute_tools(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute any tool calls in the response."""
        response = context.get("response")
        if not response or not response.has_tool_calls:
            return {}
        
        tool_results = []
        
        for tool_call in response.tool_calls:
            try:
                # Execute the tool
                result = await self._foundation.tools.execute(
                    tool_name=tool_call.name,
                    arguments=self._parse_arguments(tool_call.arguments),
                    session_id=request.session_id,
                )
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "name": tool_call.name,
                    "result": result.result if result.success else result.error,
                    "success": result.success,
                })
                
                self._metrics.tool_executions += 1
                
            except Exception as e:
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "name": tool_call.name,
                    "result": None,
                    "success": False,
                    "error": str(e),
                })
        
        # Store tool results in context
        context["tool_results"] = tool_results
        
        return {"tool_results": tool_results}

    def _parse_arguments(self, arguments: str) -> Dict[str, Any]:
        """Parse tool call arguments."""
        import json
        
        try:
            return json.loads(arguments)
        except Exception:
            return {}

    async def _update_memory(self, request: "AIRequest", context: Dict[str, Any]) -> Dict[str, Any]:
        """Update memory with new information."""
        response = context.get("response")
        if not response:
            return {}
        
        # Store the request and response in memory
        memory_data = {
            "request": request.to_dict(),
            "response": response.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Use MemoryConnector to store in memory
        memory_id = await self._foundation.memory.store(
            key=f"ai_interaction_{int(time.time() * 1000)}",
            data=memory_data,
            metadata={
                "session_id": request.session_id,
                "conversation_id": request.conversation_id,
                "model": response.model,
            },
        )
        
        return {"memory_id": memory_id}

    async def _return_result(self, request: "AIRequest", context: Dict[str, Any]) -> "AIResponse":
        """Return the final result."""
        response = context.get("response")
        if not response:
            raise ValueError("No response generated")
        
        # Add tool results to response if available
        tool_results = context.get("tool_results", [])
        if tool_results:
            for tr in tool_results:
                response.tool_results.append(
                    self._create_tool_result(tr)
                )
        
        return response

    def _create_tool_result(self, tool_result: Dict[str, Any]):
        """Create a ToolResult from a tool execution result."""
        from tangku_agentos.ai_foundation.models.response import ToolResult
        
        return ToolResult(
            tool_call_id=tool_result.get("tool_call_id", ""),
            content=tool_result.get("result"),
            role="tool",
        )

    def _generate_cache_key(self, request: "AIRequest", context: Dict[str, Any]) -> str:
        """Generate a cache key for the request."""
        import hashlib
        
        # Create a unique key based on request and context
        key_parts = [
            request.model or "",
            request.prompt or "",
            str(request.messages) if request.messages else "",
            str(request.temperature),
            str(request.max_tokens),
        ]
        
        return hashlib.sha256(":".join(key_parts).encode()).hexdigest()

    def _build_response(self, request: "AIRequest", context: Dict[str, Any]) -> "AIResponse":
        """Build a response from the execution context."""
        from tangku_agentos.ai_foundation.models.response import AIResponse, Usage, FinishReason
        
        # Get the response from context
        response = context.get("response")
        if response:
            return response
        
        # Build a default response
        return AIResponse(
            id=f"response_{int(time.time() * 1000)}",
            content="No response generated",
            role="assistant",
            model=None,
            provider=None,
            finish_reason=FinishReason.ERROR,
            usage=Usage(),
            error="No response generated",
        )

    def _build_error_response(self, request: "AIRequest", error: str) -> "AIResponse":
        """Build an error response."""
        from tangku_agentos.ai_foundation.models.response import AIResponse, Usage, FinishReason
        
        return AIResponse(
            id=f"error_{int(time.time() * 1000)}",
            content=f"Error: {error}",
            role="assistant",
            model=None,
            provider=None,
            finish_reason=FinishReason.ERROR,
            usage=Usage(),
            error=error,
        )

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the execution pipeline.
        
        Returns:
            Dictionary with execution pipeline information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "max_tokens": self._config.models.max_output_tokens,
                "temperature": self._config.models.default_temperature,
                "use_cache": self._config.cache.enabled,
                "use_memory": self._config.memory.enabled,
                "use_knowledge": self._config.knowledge.enabled,
            }
        }

    async def reset(self) -> None:
        """
        Reset the execution pipeline.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting ExecutionPipeline...")
        
        self._metrics = ExecutionPipelineMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("ExecutionPipeline reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ExecutionPipeline("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"executions={self._metrics.executions})"
        )
