"""
Runtime Communication Framework - Standard System Queries

This module defines all standard system queries for TangkuAgentOS.
These queries are used for requesting information from runtimes.

Query Naming Convention:
- Runtime queries: GetRuntimeHealth, GetRuntimeMetadata, GetRuntimeStatus
- Model queries: GetLoadedModels, GetModelInfo
- Workflow queries: GetWorkflowState, GetWorkflowHistory
- Provider queries: GetProviders, GetProviderStatus
- Memory queries: GetMemory, SearchMemory
- Knowledge queries: SearchKnowledge, GetKnowledge
- Terminal queries: GetTerminalSessions, GetTerminalSession
- Repository queries: GetRepositories, GetRepositoryInfo
- Security queries: GetPermissions, GetUserInfo
- Planning queries: GetPlanningState, GetPlan
- Automation queries: GetAutomationState, GetAutomationHistory
- Workspace queries: GetWorkspaceState, GetWorkspaceFiles

All queries follow the pattern:
- Query name: PascalCase (e.g., GetRuntimeHealth)
- Query type: lowercase with dots (e.g., "runtime.get_health")
- Parameters: Dictionary with query-specific parameters

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Query, MessageType


@dataclass
class SystemQuery:
    """
    Base class for all system queries.

    Attributes:
        query_type: Type of the query (e.g., "runtime.get_health").
        target_runtime_id: ID of the runtime to query.
        sender_id: ID of the runtime sending the query.
        parameters: Query parameters.
        timeout: Timeout in seconds.
        priority: Query priority.
        correlation_id: Correlation ID for tracing.
        metadata: Additional query metadata.
    """

    query_type: str
    target_runtime_id: Optional[str] = None
    sender_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: str = "normal"
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_query(self) -> "Query":
        """
        Convert to a Query message.

        Returns:
            Query message.
        """
        from tangku_agentos.runtime_communication import Query, MessageType

        return Query(
            message_type=MessageType.QUERY,
            sender_id=self.sender_id,
            recipient_id=self.target_runtime_id,
            query_type=self.query_type,
            payload=self.to_dict(),
            timeout=self.timeout,
            priority=self.priority,
            correlation_id=self.correlation_id,
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "query_type": self.query_type,
            "target_runtime_id": self.target_runtime_id,
            "sender_id": self.sender_id,
            "parameters": self.parameters,
            "timeout": self.timeout,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemQuery":
        """
        Create from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            SystemQuery instance.
        """
        return cls(
            query_type=data.get("query_type", ""),
            target_runtime_id=data.get("target_runtime_id"),
            sender_id=data.get("sender_id", ""),
            parameters=data.get("parameters", {}),
            timeout=data.get("timeout", 30.0),
            priority=data.get("priority", "normal"),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            metadata={k: v for k, v in data.items() if k not in (
                "query_type", "target_runtime_id", "sender_id",
                "parameters", "timeout", "priority", "correlation_id"
            )},
        )


class SystemQueries:
    """
    Factory class for creating standard system queries.

    This class provides static methods for creating all standard system queries.
    Each method returns a properly formatted SystemQuery instance.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.queries import SystemQueries
        >>> 
        >>> # Create a get runtime health query
        >>> query = SystemQueries.GetRuntimeHealth(
        ...     target_runtime_id="memory_runtime",
        ...     sender_id="kernel_runtime"
        ... )
        >>> 
        >>> # Send the query
        >>> result = await query_bus.ask(query.to_query())
    """

    # =========================================================================
    # RUNTIME QUERIES
    # =========================================================================

    @staticmethod
    def GetRuntimeHealth(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_health query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_health",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeStatus(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_status query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeMetadata(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_metadata query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_metadata",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeCapabilities(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_capabilities query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_capabilities",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeMetrics(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        metric_names: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_metrics query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            metric_names: List of specific metrics to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"metric_names": metric_names or [], **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeConfig(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_config query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_config",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListRuntimes(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.list query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for runtimes.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRuntimeDependencies(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a runtime.get_dependencies query.

        Args:
            target_runtime_id: ID of the runtime to query.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="runtime.get_dependencies",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # MODEL QUERIES
    # =========================================================================

    @staticmethod
    def GetLoadedModels(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a model.get_loaded query.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for models.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="model.get_loaded",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetModelInfo(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        model_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a model.get_info query.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            model_id: ID of the model to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="model.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"model_id": model_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetModelCapabilities(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        model_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a model.get_capabilities query.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            model_id: ID of the model to get capabilities for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="model.get_capabilities",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"model_id": model_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetModelStats(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        model_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a model.get_stats query.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            model_id: ID of the model to get stats for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="model.get_stats",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"model_id": model_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListModelTypes(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a model.list_types query.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="model.list_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # WORKFLOW QUERIES
    # =========================================================================

    @staticmethod
    def GetWorkflowState(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workflow_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.get_state query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workflow_id: ID of the workflow to get state for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkflowHistory(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workflow_id: str = "",
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.get_history query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workflow_id: ID of the workflow to get history for.
            limit: Maximum number of history entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.get_history",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkflowResult(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workflow_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.get_result query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workflow_id: ID of the workflow to get result for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.get_result",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListWorkflows(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.list query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for workflows.
            limit: Maximum number of workflows to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkflowTypes(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.list_types query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.list_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkflowMetrics(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workflow_id: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workflow.get_metrics query.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workflow_id: Optional ID of a specific workflow to get metrics for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workflow.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # PROVIDER QUERIES
    # =========================================================================

    @staticmethod
    def GetProviders(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a provider.get query.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for providers.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="provider.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetProviderStatus(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        provider_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a provider.get_status query.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            provider_id: ID of the provider to get status for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="provider.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetProviderCapabilities(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        provider_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a provider.get_capabilities query.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            provider_id: ID of the provider to get capabilities for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="provider.get_capabilities",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetProviderConfig(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        provider_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a provider.get_config query.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            provider_id: ID of the provider to get config for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="provider.get_config",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListProviderTypes(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a provider.list_types query.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="provider.list_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # MEMORY QUERIES
    # =========================================================================

    @staticmethod
    def GetMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        memory_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a memory.get query.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            memory_id: ID of the memory to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="memory.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"memory_id": memory_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SearchMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a memory.search query.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="memory.search",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "query": query,
                "filter": filter or {},
                "limit": limit,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListMemories(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a memory.list query.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for memories.
            limit: Maximum number of memories to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="memory.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetMemoryStats(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a memory.get_stats query.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="memory.get_stats",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetMemoryTypes(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a memory.get_types query.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="memory.get_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # KNOWLEDGE QUERIES
    # =========================================================================

    @staticmethod
    def SearchKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a knowledge.search query.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="knowledge.search",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "query": query,
                "filter": filter or {},
                "limit": limit,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        document_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a knowledge.get query.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            document_id: ID of the document to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="knowledge.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"document_id": document_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a knowledge.list query.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for knowledge.
            limit: Maximum number of knowledge items to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="knowledge.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetKnowledgeStats(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a knowledge.get_stats query.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="knowledge.get_stats",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetKnowledgeSources(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a knowledge.get_sources query.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="knowledge.get_sources",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # TERMINAL QUERIES
    # =========================================================================

    @staticmethod
    def GetTerminalSessions(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a terminal.get_sessions query.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for sessions.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="terminal.get_sessions",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetTerminalSession(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        session_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a terminal.get_session query.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            session_id: ID of the session to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="terminal.get_session",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"session_id": session_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetTerminalOutput(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        session_id: str = "",
        command_id: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a terminal.get_output query.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            session_id: ID of the session.
            command_id: Optional ID of a specific command to get output for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="terminal.get_output",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"session_id": session_id, "command_id": command_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetTerminalHistory(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        session_id: str = "",
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a terminal.get_history query.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            session_id: ID of the session.
            limit: Maximum number of history entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="terminal.get_history",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"session_id": session_id, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # REPOSITORY QUERIES
    # =========================================================================

    @staticmethod
    def GetRepositories(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a repository.get query.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for repositories.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="repository.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRepositoryInfo(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        repository_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a repository.get_info query.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            repository_id: ID of the repository to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="repository.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"repository_id": repository_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRepositoryStatus(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        repository_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a repository.get_status query.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            repository_id: ID of the repository to get status for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="repository.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"repository_id": repository_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SearchRepository(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        repository_id: str = "",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a repository.search query.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            repository_id: ID of the repository to search.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="repository.search",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "repository_id": repository_id,
                "query": query,
                "filter": filter or {},
                "limit": limit,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListRepositoryTypes(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a repository.list_types query.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="repository.list_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # SECURITY QUERIES
    # =========================================================================

    @staticmethod
    def GetPermissions(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a security.get_permissions query.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            user_id: Optional ID of the user to get permissions for.
            resource: Optional resource to check permissions for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="security.get_permissions",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"user_id": user_id, "resource": resource, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetUserInfo(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        user_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a security.get_user_info query.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            user_id: ID of the user to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="security.get_user_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"user_id": user_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetRoles(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a security.get_roles query.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            user_id: Optional ID of the user to get roles for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="security.get_roles",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"user_id": user_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def CheckAccess(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        user_id: str = "",
        action: str = "",
        resource: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a security.check_access query.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            user_id: ID of the user to check access for.
            action: Action to check.
            resource: Resource to check access to.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="security.check_access",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "user_id": user_id,
                "action": action,
                "resource": resource,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAuditLog(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a security.get_audit_log query.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for audit log entries.
            limit: Maximum number of entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="security.get_audit_log",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # PLANNING QUERIES
    # =========================================================================

    @staticmethod
    def GetPlanningState(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a planning.get_state query.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="planning.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetPlan(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        plan_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a planning.get_plan query.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            plan_id: ID of the plan to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="planning.get_plan",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListPlans(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a planning.list_plans query.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for plans.
            limit: Maximum number of plans to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="planning.list_plans",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetPlanHistory(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        plan_id: str = "",
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a planning.get_plan_history query.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            plan_id: ID of the plan to get history for.
            limit: Maximum number of history entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="planning.get_plan_history",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetPlanMetrics(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        plan_id: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a planning.get_metrics query.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            plan_id: Optional ID of a specific plan to get metrics for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="planning.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # AUTOMATION QUERIES
    # =========================================================================

    @staticmethod
    def GetAutomationState(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an automation.get_state query.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="automation.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAutomationStatus(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        automation_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an automation.get_status query.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            automation_id: ID of the automation to get status for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="automation.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAutomationHistory(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        automation_id: str = "",
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create an automation.get_history query.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            automation_id: ID of the automation to get history for.
            limit: Maximum number of history entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="automation.get_history",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListAutomations(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create an automation.list query.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for automations.
            limit: Maximum number of automations to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="automation.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAutomationMetrics(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        automation_id: Optional[str] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create an automation.get_metrics query.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            automation_id: Optional ID of a specific automation to get metrics for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="automation.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # WORKSPACE QUERIES
    # =========================================================================

    @staticmethod
    def GetWorkspaceState(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.get_state query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkspaceInfo(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workspace_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.get_info query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workspace_id: ID of the workspace to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workspace_id": workspace_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListWorkspaces(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.list query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for workspaces.
            limit: Maximum number of workspaces to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkspaceFiles(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workspace_id: str = "",
        path: str = "/",
        recursive: bool = False,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.get_files query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workspace_id: ID of the workspace.
            path: Path to list files from.
            recursive: Whether to list recursively.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.get_files",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "path": path,
                "recursive": recursive,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetFileInfo(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workspace_id: str = "",
        file_path: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.get_file_info query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workspace_id: ID of the workspace.
            file_path: Path of the file to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.get_file_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workspace_id": workspace_id, "file_path": file_path, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ReadFile(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workspace_id: str = "",
        file_path: str = "",
        encoding: str = "utf-8",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a workspace.read_file query.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            workspace_id: ID of the workspace.
            file_path: Path of the file to read.
            encoding: File encoding.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="workspace.read_file",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "file_path": file_path,
                "encoding": encoding,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # REASONING QUERIES
    # =========================================================================

    @staticmethod
    def GetReasoningState(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a reasoning.get_state query.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="reasoning.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetReasoningSession(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        reasoning_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a reasoning.get_session query.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            reasoning_id: ID of the reasoning session to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="reasoning.get_session",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reasoning_id": reasoning_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListReasoningSessions(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a reasoning.list_sessions query.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for reasoning sessions.
            limit: Maximum number of sessions to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="reasoning.list_sessions",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetReasoningHistory(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        reasoning_id: str = "",
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a reasoning.get_history query.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            reasoning_id: ID of the reasoning session to get history for.
            limit: Maximum number of history entries to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="reasoning.get_history",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reasoning_id": reasoning_id, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # COORDINATION QUERIES
    # =========================================================================

    @staticmethod
    def GetCoordinationState(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a coordination.get_state query.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="coordination.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetTaskStatus(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        task_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a coordination.get_task_status query.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            task_id: ID of the task to get status for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="coordination.get_task_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"task_id": task_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListTasks(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a coordination.list_tasks query.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for tasks.
            limit: Maximum number of tasks to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="coordination.list_tasks",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkerStatus(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        worker_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a coordination.get_worker_status query.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            worker_id: ID of the worker to get status for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="coordination.get_worker_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"worker_id": worker_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListWorkers(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a coordination.list_workers query.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for workers.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="coordination.list_workers",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # CONTEXT ENGINE QUERIES
    # =========================================================================

    @staticmethod
    def GetContextState(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a context.get_state query.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="context.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetContext(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        context_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a context.get query.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            context_id: ID of the context to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="context.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"context_id": context_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListContexts(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a context.list query.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for contexts.
            limit: Maximum number of contexts to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="context.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetContextTypes(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a context.get_types query.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="context.get_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # DECISION QUERIES
    # =========================================================================

    @staticmethod
    def GetDecisionState(
        target_runtime_id: str = "decision_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a decision.get_state query.

        Args:
            target_runtime_id: ID of the decision runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="decision.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetDecision(
        target_runtime_id: str = "decision_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        decision_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a decision.get query.

        Args:
            target_runtime_id: ID of the decision runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            decision_id: ID of the decision to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="decision.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"decision_id": decision_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListDecisions(
        target_runtime_id: str = "decision_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create a decision.list query.

        Args:
            target_runtime_id: ID of the decision runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for decisions.
            limit: Maximum number of decisions to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="decision.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # AGENT FRAMEWORK QUERIES
    # =========================================================================

    @staticmethod
    def GetAgentState(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an agent.get_state query.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="agent.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAgentInfo(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        agent_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an agent.get_info query.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            agent_id: ID of the agent to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="agent.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListAgents(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs,
    ) -> SystemQuery:
        """
        Create an agent.list query.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            filter: Filter criteria for agents.
            limit: Maximum number of agents to return.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="agent.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, "limit": limit, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAgentTypes(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an agent.get_types query.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="agent.get_types",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAgentCapabilities(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        agent_id: str = "",
        **kwargs,
    ) -> SystemQuery:
        """
        Create an agent.get_capabilities query.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            agent_id: ID of the agent to get capabilities for.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="agent.get_capabilities",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # SYSTEM QUERIES
    # =========================================================================

    @staticmethod
    def GetSystemState(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.get_state query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetSystemMetrics(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.get_metrics query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetSystemConfig(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.get_config query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.get_config",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetSystemInfo(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.get_info query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def Ping(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "low",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.ping query.

        Args:
            target_runtime_id: ID of the runtime to ping.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.ping",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetVersion(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemQuery:
        """
        Create a system.get_version query.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the query.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional parameters.

        Returns:
            SystemQuery instance.
        """
        return SystemQuery(
            query_type="system.get_version",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )
