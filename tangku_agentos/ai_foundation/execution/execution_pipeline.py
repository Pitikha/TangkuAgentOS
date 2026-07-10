"""
Execution Pipeline for TangkuAgentOS AI Foundation Framework.

Defines the AI execution pipeline, from request to response.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
from ..sessions.session_manager import SessionManager, AISession
from ..conversations.conversation_manager import ConversationManager
from ..context.context_assembler import ContextAssembler
from ..memory.memory_connector import MemoryConnector
from ..knowledge.knowledge_connector import KnowledgeConnector
from ..models.base_model import AIModel
from ..validation.output_validator import OutputValidator
from ..guardrails.guardrail_engine import GuardrailEngine
from ..monitoring.metrics_collector import MetricsCollector
from ..caching.response_cache import ResponseCache
from ..budgeting.token_budget_manager import TokenBudgetManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of an execution pipeline operation."""
    request: Dict[str, Any]
    response: Dict[str, Any]
    context: Dict[str, Any]
    metrics: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionPipeline:
    """Manages the end-to-end execution pipeline for AI requests in TangkuAgentOS.

    This class provides the full pipeline for executing AI requests,
    including context assembly, memory/knowledge retrieval, model execution,
    validation, and response generation.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        conversation_manager: ConversationManager,
        context_assembler: ContextAssembler,
        memory_connector: MemoryConnector,
        knowledge_connector: KnowledgeConnector,
        output_validator: OutputValidator,
        guardrail_engine: GuardrailEngine,
        metrics_collector: MetricsCollector,
        response_cache: ResponseCache,
        token_budget_manager: TokenBudgetManager,
    ):
        """Initialize the ExecutionPipeline.

        Args:
            session_manager: The SessionManager instance to use.
            conversation_manager: The ConversationManager instance to use.
            context_assembler: The ContextAssembler instance to use.
            memory_connector: The MemoryConnector instance to use.
            knowledge_connector: The KnowledgeConnector instance to use.
            output_validator: The OutputValidator instance to use.
            guardrail_engine: The GuardrailEngine instance to use.
            metrics_collector: The MetricsCollector instance to use.
            response_cache: The ResponseCache instance to use.
            token_budget_manager: The TokenBudgetManager instance to use.
        """
        self._session_manager = session_manager
        self._conversation_manager = conversation_manager
        self._context_assembler = context_assembler
        self._memory_connector = memory_connector
        self._knowledge_connector = knowledge_connector
        self._output_validator = output_validator
        self._guardrail_engine = guardrail_engine
        self._metrics_collector = metrics_collector
        self._response_cache = response_cache
        self._token_budget_manager = token_budget_manager
        logger.info("ExecutionPipeline initialized.")

    async def execute(
        self,
        request: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> PipelineResult:
        """Execute an AI request through the full pipeline.

        Args:
            request: The AI request to execute.
            session_id: Optional session ID for the request.

        Returns:
            PipelineResult containing the request, response, context, and metrics.
        """
        # Step 1: Validate the request
        validated_request = self._validate_request(request)

        # Step 2: Get or create a session
        session = self._get_session(session_id, validated_request)

        # Step 3: Assemble context
        context = await self._assemble_context(session, validated_request)

        # Step 4: Retrieve memory and knowledge
        memory_context = await self._retrieve_memory(session)
        knowledge_context = await self._retrieve_knowledge(session)

        # Step 5: Select model (from session or request)
        model = self._select_model(session, validated_request)

        # Step 6: Build prompt
        prompt = self._build_prompt(context, memory_context, knowledge_context, validated_request)

        # Step 7: Estimate tokens
        token_estimate = self._token_budget_manager.estimate_tokens(prompt)

        # Step 8: Check cache
        cached_response = self._response_cache.get(prompt)
        if cached_response:
            return PipelineResult(
                request=validated_request,
                response=cached_response,
                context=context,
                metrics={"cached": True, "tokens": token_estimate},
            )

        # Step 9: Execute model
        response = await self._execute_model(model, prompt, token_estimate)

        # Step 10: Validate output
        validated_response = self._output_validator.validate(response)

        # Step 11: Apply guardrails
        guarded_response = self._guardrail_engine.apply_guardrails(validated_response)

        # Step 12: Update memory (if needed)
        await self._update_memory(session, guarded_response)

        # Step 13: Cache response
        self._response_cache.set(prompt, guarded_response)

        # Step 14: Collect metrics
        metrics = self._metrics_collector.collect(
            session=session,
            request=validated_request,
            response=guarded_response,
            tokens=token_estimate,
        )

        logger.info(f"Executed request through pipeline: {validated_request.get('prompt', '')[:50]}...")
        return PipelineResult(
            request=validated_request,
            response=guarded_response,
            context=context,
            metrics=metrics,
        )

    def _validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the incoming request.

        Args:
            request: The request to validate.

        Returns:
            The validated request.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.get("prompt") and not request.get("messages"):
            raise ValueError("Request must include a prompt or messages.")
        return request

    def _get_session(
        self,
        session_id: Optional[str],
        request: Dict[str, Any],
    ) -> AISession:
        """Get or create a session for the request.

        Args:
            session_id: Optional session ID.
            request: The validated request.

        Returns:
            The AISession for the request.
        """
        if session_id:
            session = self._session_manager.get_session(session_id)
            if session:
                return session
        # Create a new session (placeholder: use actual provider/model)
        from ..providers.openai_provider import OpenAIProvider, OpenAIModel
        provider = OpenAIProvider(api_key="placeholder")
        model = OpenAIModel("gpt-4", "placeholder")
        return self._session_manager.create_session(model, provider)

    async def _assemble_context(
        self,
        session: AISession,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assemble context for the request.

        Args:
            session: The AISession for the request.
            request: The validated request.

        Returns:
            The assembled context.
        """
        conversation = self._conversation_manager.get_conversation(session.session_id)
        return await self._context_assembler.assemble_context(session, conversation)

    async def _retrieve_memory(self, session: AISession) -> Dict[str, Any]:
        """Retrieve relevant memories for the session.

        Args:
            session: The AISession for the request.

        Returns:
            Dictionary of relevant memories.
        """
        return await self._memory_connector.retrieve(session.memory_references)

    async def _retrieve_knowledge(self, session: AISession) -> Dict[str, Any]:
        """Retrieve relevant knowledge for the session.

        Args:
            session: The AISession for the request.

        Returns:
            Dictionary of relevant knowledge.
        """
        return await self._knowledge_connector.retrieve(session.knowledge_references)

    def _select_model(
        self,
        session: AISession,
        request: Dict[str, Any],
    ) -> AIModel:
        """Select the model for the request.

        Args:
            session: The AISession for the request.
            request: The validated request.

        Returns:
            The selected AIModel.
        """
        return session.model

    def _build_prompt(
        self,
        context: Dict[str, Any],
        memory_context: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        request: Dict[str, Any],
    ) -> str:
        """Build the prompt for the AI model.

        Args:
            context: The assembled context.
            memory_context: The retrieved memory context.
            knowledge_context: The retrieved knowledge context.
            request: The validated request.

        Returns:
            The built prompt.
        """
        prompt_parts = []
        if request.get("prompt"):
            prompt_parts.append(request["prompt"])
        elif request.get("messages"):
            prompt_parts.append("\n".join([msg.get("content", "") for msg in request["messages"]]))
        if memory_context:
            prompt_parts.append("\n\nMemory Context:")
            prompt_parts.append(str(memory_context))
        if knowledge_context:
            prompt_parts.append("\n\nKnowledge Context:")
            prompt_parts.append(str(knowledge_context))
        return "\n".join(prompt_parts)

    async def _execute_model(
        self,
        model: AIModel,
        prompt: str,
        token_estimate: int,
    ) -> Dict[str, Any]:
        """Execute the AI model with the prompt.

        Args:
            model: The AIModel to use.
            prompt: The prompt to execute.
            token_estimate: The estimated number of tokens in the prompt.

        Returns:
            The model's response.
        """
        if token_estimate > model.capabilities.max_context:
            raise ValueError("Prompt exceeds model's maximum context length.")
        return await model.chat([{"role": "user", "content": prompt}])

    async def _update_memory(
        self,
        session: AISession,
        response: Dict[str, Any],
    ) -> None:
        """Update memory based on the response.

        Args:
            session: The AISession for the request.
            response: The model's response.
        """
        # Placeholder: In a real implementation, this would update memory
        pass
