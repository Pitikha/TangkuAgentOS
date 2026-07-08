"""
Runtime Communication Framework - Standard System Events

This module defines all standard system events for TangkuAgentOS.
These events are used for system-level communication between runtimes.

All runtimes should publish and subscribe to these events as appropriate.

Event Naming Convention:
- runtime.*: Runtime lifecycle events
- kernel.*: Kernel events
- memory.*: Memory engine events
- knowledge.*: Knowledge engine events
- workflow.*: Workflow engine events
- provider.*: Provider runtime events
- model.*: Model runtime events
- terminal.*: Terminal runtime events
- repository.*: Repository intelligence events
- security.*: Security engine events
- planning.*: Planning runtime events
- automation.*: Automation runtime events
- workspace.*: Workspace engine events

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Event, MessageType


@dataclass
class SystemEvent:
    """
    Base class for all system events.

    Attributes:
        event_type: Type of the event (e.g., "runtime.started").
        runtime_id: ID of the runtime that published the event.
        timestamp: When the event occurred.
        correlation_id: Correlation ID for tracing.
        metadata: Additional event metadata.
    """

    event_type: str
    runtime_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_event(self) -> "Event":
        """
        Convert to an Event message.

        Returns:
            Event message.
        """
        from tangku_agentos.runtime_communication import Event, MessageType

        return Event(
            message_type=MessageType.EVENT,
            sender_id=self.runtime_id,
            event_type=self.event_type,
            payload=self.to_dict(),
            timestamp=self.timestamp,
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
            "event_type": self.event_type,
            "runtime_id": self.runtime_id,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemEvent":
        """
        Create from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            SystemEvent instance.
        """
        return cls(
            event_type=data.get("event_type", ""),
            runtime_id=data.get("runtime_id", ""),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            metadata={k: v for k, v in data.items() if k not in (
                "event_type", "runtime_id", "timestamp", "correlation_id"
            )},
        )


class SystemEvents:
    """
    Factory class for creating standard system events.

    This class provides static methods for creating all standard system events.
    Each method returns a properly formatted SystemEvent instance.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.events import SystemEvents
        >>> 
        >>> # Create a runtime started event
        >>> event = SystemEvents.runtime_started(
        ...     runtime_id="memory_runtime",
        ...     name="Memory Runtime",
        ...     version="1.0.0"
        ... )
        >>> 
        >>> # Publish the event
        >>> await event_bus.publish(event.to_event())
    """

    # =========================================================================
    # RUNTIME LIFECYCLE EVENTS
    # =========================================================================

    @staticmethod
    def runtime_registered(
        runtime_id: str,
        name: str,
        type: str,
        version: str = "1.0.0",
        capabilities: Optional[list] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.registered event.

        Published when a runtime registers with the runtime registry.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            version: Version of the runtime.
            capabilities: List of runtime capabilities.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "version": version,
            "capabilities": capabilities or [],
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.registered",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_unregistered(
        runtime_id: str,
        name: str,
        type: str,
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.unregistered event.

        Published when a runtime unregisters from the runtime registry.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            reason: Reason for unregistration.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.unregistered",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_started(
        runtime_id: str,
        name: str,
        type: str,
        version: str = "1.0.0",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.started event.

        Published when a runtime starts successfully.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            version: Version of the runtime.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "version": version,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_stopped(
        runtime_id: str,
        name: str,
        type: str,
        version: str = "1.0.0",
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.stopped event.

        Published when a runtime stops.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            version: Version of the runtime.
            reason: Reason for stopping.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "version": version,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.stopped",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_failed(
        runtime_id: str,
        name: str,
        type: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.failed event.

        Published when a runtime fails.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_paused(
        runtime_id: str,
        name: str,
        type: str,
        reason: str = "manual",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.paused event.

        Published when a runtime is paused.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            reason: Reason for pausing.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.paused",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_resumed(
        runtime_id: str,
        name: str,
        type: str,
        reason: str = "manual",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.resumed event.

        Published when a runtime is resumed.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            reason: Reason for resuming.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.resumed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_degraded(
        runtime_id: str,
        name: str,
        type: str,
        reason: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.degraded event.

        Published when a runtime enters a degraded state.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            reason: Reason for degradation.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.degraded",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def runtime_recovered(
        runtime_id: str,
        name: str,
        type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a runtime.recovered event.

        Published when a runtime recovers from a degraded state.

        Args:
            runtime_id: ID of the runtime.
            name: Human-readable name of the runtime.
            type: Type of the runtime.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "name": name,
            "type": type,
            **kwargs,
        }
        return SystemEvent(
            event_type="runtime.recovered",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # KERNEL EVENTS
    # =========================================================================

    @staticmethod
    def kernel_started(
        version: str = "1.0.0",
        build_info: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a kernel.started event.

        Published when the kernel starts.

        Args:
            version: Kernel version.
            build_info: Build information.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "version": version,
            "build_info": build_info or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="kernel.started",
            runtime_id="kernel_runtime",
            metadata=metadata,
        )

    @staticmethod
    def kernel_shutdown(
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a kernel.shutdown event.

        Published when the kernel shuts down.

        Args:
            reason: Reason for shutdown.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="kernel.shutdown",
            runtime_id="kernel_runtime",
            metadata=metadata,
        )

    @staticmethod
    def kernel_error(
        error: str,
        error_type: str = "unknown",
        severity: str = "error",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a kernel.error event.

        Published when the kernel encounters an error.

        Args:
            error: Error message.
            error_type: Type of error.
            severity: Error severity (info, warning, error, critical).
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "error": error,
            "error_type": error_type,
            "severity": severity,
            **kwargs,
        }
        return SystemEvent(
            event_type="kernel.error",
            runtime_id="kernel_runtime",
            metadata=metadata,
        )

    @staticmethod
    def kernel_ready(
        version: str = "1.0.0",
        runtimes_loaded: int = 0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a kernel.ready event.

        Published when the kernel is fully ready.

        Args:
            version: Kernel version.
            runtimes_loaded: Number of runtimes loaded.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "version": version,
            "runtimes_loaded": runtimes_loaded,
            **kwargs,
        }
        return SystemEvent(
            event_type="kernel.ready",
            runtime_id="kernel_runtime",
            metadata=metadata,
        )

    # =========================================================================
    # MEMORY ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def memory_updated(
        runtime_id: str = "memory_engine",
        operation: str = "update",
        memory_id: Optional[str] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a memory.updated event.

        Published when memory is updated.

        Args:
            runtime_id: ID of the memory runtime.
            operation: Type of operation (create, update, delete).
            memory_id: ID of the memory.
            size: Size of the memory.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "operation": operation,
            "memory_id": memory_id,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="memory.updated",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def memory_loaded(
        runtime_id: str = "memory_engine",
        memory_id: str,
        size: int,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a memory.loaded event.

        Published when a memory is loaded.

        Args:
            runtime_id: ID of the memory runtime.
            memory_id: ID of the memory.
            size: Size of the memory.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "memory_id": memory_id,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="memory.loaded",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def memory_saved(
        runtime_id: str = "memory_engine",
        memory_id: str,
        size: int,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a memory.saved event.

        Published when a memory is saved.

        Args:
            runtime_id: ID of the memory runtime.
            memory_id: ID of the memory.
            size: Size of the memory.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "memory_id": memory_id,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="memory.saved",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def memory_deleted(
        runtime_id: str = "memory_engine",
        memory_id: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a memory.deleted event.

        Published when a memory is deleted.

        Args:
            runtime_id: ID of the memory runtime.
            memory_id: ID of the memory.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "memory_id": memory_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="memory.deleted",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # KNOWLEDGE ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def knowledge_updated(
        runtime_id: str = "knowledge_engine",
        operation: str = "update",
        knowledge_id: Optional[str] = None,
        source: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a knowledge.updated event.

        Published when knowledge is updated.

        Args:
            runtime_id: ID of the knowledge runtime.
            operation: Type of operation.
            knowledge_id: ID of the knowledge.
            source: Source of the knowledge.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "operation": operation,
            "knowledge_id": knowledge_id,
            "source": source,
            **kwargs,
        }
        return SystemEvent(
            event_type="knowledge.updated",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def knowledge_indexed(
        runtime_id: str = "knowledge_engine",
        document_id: str,
        source: str,
        size: int,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a knowledge.indexed event.

        Published when a document is indexed.

        Args:
            runtime_id: ID of the knowledge runtime.
            document_id: ID of the document.
            source: Source of the document.
            size: Size of the document.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "document_id": document_id,
            "source": source,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="knowledge.indexed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def knowledge_searched(
        runtime_id: str = "knowledge_engine",
        query: str,
        results_count: int,
        duration_ms: float,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a knowledge.searched event.

        Published when a knowledge search is performed.

        Args:
            runtime_id: ID of the knowledge runtime.
            query: Search query.
            results_count: Number of results.
            duration_ms: Duration of the search in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "query": query,
            "results_count": results_count,
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="knowledge.searched",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # WORKFLOW ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def workflow_started(
        runtime_id: str = "workflow_engine",
        workflow_id: str,
        workflow_type: str,
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workflow.started event.

        Published when a workflow starts.

        Args:
            runtime_id: ID of the workflow runtime.
            workflow_id: ID of the workflow.
            workflow_type: Type of the workflow.
            input_data: Input data for the workflow.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "input_data": input_data or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="workflow.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workflow_step_completed(
        runtime_id: str = "workflow_engine",
        workflow_id: str,
        step_id: str,
        step_name: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workflow.step_completed event.

        Published when a workflow step completes.

        Args:
            runtime_id: ID of the workflow runtime.
            workflow_id: ID of the workflow.
            step_id: ID of the step.
            step_name: Name of the step.
            result: Result of the step.
            duration_ms: Duration of the step in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "step_name": step_name,
            "result": result or {},
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="workflow.step_completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workflow_completed(
        runtime_id: str = "workflow_engine",
        workflow_id: str,
        workflow_type: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        status: str = "completed",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workflow.completed event.

        Published when a workflow completes.

        Args:
            runtime_id: ID of the workflow runtime.
            workflow_id: ID of the workflow.
            workflow_type: Type of the workflow.
            result: Result of the workflow.
            duration_ms: Duration of the workflow in milliseconds.
            status: Completion status (completed, failed, cancelled).
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "result": result or {},
            "duration_ms": duration_ms,
            "status": status,
            **kwargs,
        }
        return SystemEvent(
            event_type="workflow.completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workflow_failed(
        runtime_id: str = "workflow_engine",
        workflow_id: str,
        workflow_type: str,
        error: str,
        error_type: str = "unknown",
        step_id: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workflow.failed event.

        Published when a workflow fails.

        Args:
            runtime_id: ID of the workflow runtime.
            workflow_id: ID of the workflow.
            workflow_type: Type of the workflow.
            error: Error message.
            error_type: Type of error.
            step_id: ID of the step that failed.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "error": error,
            "error_type": error_type,
            "step_id": step_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="workflow.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # PROVIDER RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def provider_connected(
        runtime_id: str = "provider_runtime",
        provider_id: str,
        provider_type: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a provider.connected event.

        Published when a provider connects.

        Args:
            runtime_id: ID of the provider runtime.
            provider_id: ID of the provider.
            provider_type: Type of the provider.
            config: Provider configuration.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "provider_id": provider_id,
            "provider_type": provider_type,
            "config": config or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="provider.connected",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def provider_disconnected(
        runtime_id: str = "provider_runtime",
        provider_id: str,
        provider_type: str,
        reason: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a provider.disconnected event.

        Published when a provider disconnects.

        Args:
            runtime_id: ID of the provider runtime.
            provider_id: ID of the provider.
            provider_type: Type of the provider.
            reason: Reason for disconnection.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "provider_id": provider_id,
            "provider_type": provider_type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="provider.disconnected",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def provider_error(
        runtime_id: str = "provider_runtime",
        provider_id: str,
        provider_type: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a provider.error event.

        Published when a provider encounters an error.

        Args:
            runtime_id: ID of the provider runtime.
            provider_id: ID of the provider.
            provider_type: Type of the provider.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "provider_id": provider_id,
            "provider_type": provider_type,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="provider.error",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def provider_rate_limited(
        runtime_id: str = "provider_runtime",
        provider_id: str,
        provider_type: str,
        retry_after: Optional[float] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a provider.rate_limited event.

        Published when a provider is rate limited.

        Args:
            runtime_id: ID of the provider runtime.
            provider_id: ID of the provider.
            provider_type: Type of the provider.
            retry_after: Seconds until retry is allowed.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "provider_id": provider_id,
            "provider_type": provider_type,
            "retry_after": retry_after,
            **kwargs,
        }
        return SystemEvent(
            event_type="provider.rate_limited",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # MODEL RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def model_loaded(
        runtime_id: str = "model_runtime",
        model_id: str,
        model_name: str,
        model_type: str,
        size: Optional[int] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a model.loaded event.

        Published when a model is loaded.

        Args:
            runtime_id: ID of the model runtime.
            model_id: ID of the model.
            model_name: Name of the model.
            model_type: Type of the model.
            size: Size of the model in bytes.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "model_id": model_id,
            "model_name": model_name,
            "model_type": model_type,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="model.loaded",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def model_unloaded(
        runtime_id: str = "model_runtime",
        model_id: str,
        model_name: str,
        model_type: str,
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a model.unloaded event.

        Published when a model is unloaded.

        Args:
            runtime_id: ID of the model runtime.
            model_id: ID of the model.
            model_name: Name of the model.
            model_type: Type of the model.
            reason: Reason for unloading.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "model_id": model_id,
            "model_name": model_name,
            "model_type": model_type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="model.unloaded",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def model_inference_started(
        runtime_id: str = "model_runtime",
        model_id: str,
        inference_id: str,
        input_tokens: Optional[int] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a model.inference_started event.

        Published when a model inference starts.

        Args:
            runtime_id: ID of the model runtime.
            model_id: ID of the model.
            inference_id: ID of the inference.
            input_tokens: Number of input tokens.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "model_id": model_id,
            "inference_id": inference_id,
            "input_tokens": input_tokens,
            **kwargs,
        }
        return SystemEvent(
            event_type="model.inference_started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def model_inference_completed(
        runtime_id: str = "model_runtime",
        model_id: str,
        inference_id: str,
        output_tokens: Optional[int] = None,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a model.inference_completed event.

        Published when a model inference completes.

        Args:
            runtime_id: ID of the model runtime.
            model_id: ID of the model.
            inference_id: ID of the inference.
            output_tokens: Number of output tokens.
            duration_ms: Duration of the inference in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "model_id": model_id,
            "inference_id": inference_id,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="model.inference_completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def model_inference_failed(
        runtime_id: str = "model_runtime",
        model_id: str,
        inference_id: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a model.inference_failed event.

        Published when a model inference fails.

        Args:
            runtime_id: ID of the model runtime.
            model_id: ID of the model.
            inference_id: ID of the inference.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "model_id": model_id,
            "inference_id": inference_id,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="model.inference_failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # TERMINAL RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def terminal_command_executed(
        runtime_id: str = "terminal_runtime",
        command_id: str,
        command: str,
        exit_code: int,
        duration_ms: float = 0.0,
        output: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a terminal.command.executed event.

        Published when a terminal command executes.

        Args:
            runtime_id: ID of the terminal runtime.
            command_id: ID of the command.
            command: The command that was executed.
            exit_code: Exit code of the command.
            duration_ms: Duration of the command in milliseconds.
            output: Command output.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "command_id": command_id,
            "command": command,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output": output,
            **kwargs,
        }
        return SystemEvent(
            event_type="terminal.command.executed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def terminal_command_started(
        runtime_id: str = "terminal_runtime",
        command_id: str,
        command: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a terminal.command.started event.

        Published when a terminal command starts.

        Args:
            runtime_id: ID of the terminal runtime.
            command_id: ID of the command.
            command: The command being executed.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "command_id": command_id,
            "command": command,
            **kwargs,
        }
        return SystemEvent(
            event_type="terminal.command.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def terminal_command_failed(
        runtime_id: str = "terminal_runtime",
        command_id: str,
        command: str,
        error: str,
        exit_code: int = 1,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a terminal.command.failed event.

        Published when a terminal command fails.

        Args:
            runtime_id: ID of the terminal runtime.
            command_id: ID of the command.
            command: The command that failed.
            error: Error message.
            exit_code: Exit code of the command.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "command_id": command_id,
            "command": command,
            "error": error,
            "exit_code": exit_code,
            **kwargs,
        }
        return SystemEvent(
            event_type="terminal.command.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def terminal_session_started(
        runtime_id: str = "terminal_runtime",
        session_id: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a terminal.session.started event.

        Published when a terminal session starts.

        Args:
            runtime_id: ID of the terminal runtime.
            session_id: ID of the session.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "session_id": session_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="terminal.session.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def terminal_session_ended(
        runtime_id: str = "terminal_runtime",
        session_id: str,
        reason: str = "exit",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a terminal.session.ended event.

        Published when a terminal session ends.

        Args:
            runtime_id: ID of the terminal runtime.
            session_id: ID of the session.
            reason: Reason for ending.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "session_id": session_id,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="terminal.session.ended",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # REPOSITORY INTELLIGENCE EVENTS
    # =========================================================================

    @staticmethod
    def repository_indexed(
        runtime_id: str = "repository_intelligence",
        repository_id: str,
        repository_type: str,
        repository_url: str,
        items_indexed: int,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a repository.indexed event.

        Published when a repository is indexed.

        Args:
            runtime_id: ID of the repository intelligence runtime.
            repository_id: ID of the repository.
            repository_type: Type of the repository.
            repository_url: URL of the repository.
            items_indexed: Number of items indexed.
            duration_ms: Duration of indexing in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "repository_id": repository_id,
            "repository_type": repository_type,
            "repository_url": repository_url,
            "items_indexed": items_indexed,
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="repository.indexed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def repository_sync_started(
        runtime_id: str = "repository_intelligence",
        repository_id: str,
        repository_type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a repository.sync_started event.

        Published when a repository sync starts.

        Args:
            runtime_id: ID of the repository intelligence runtime.
            repository_id: ID of the repository.
            repository_type: Type of the repository.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "repository_id": repository_id,
            "repository_type": repository_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="repository.sync_started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def repository_sync_completed(
        runtime_id: str = "repository_intelligence",
        repository_id: str,
        repository_type: str,
        items_synced: int,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a repository.sync_completed event.

        Published when a repository sync completes.

        Args:
            runtime_id: ID of the repository intelligence runtime.
            repository_id: ID of the repository.
            repository_type: Type of the repository.
            items_synced: Number of items synced.
            duration_ms: Duration of sync in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "repository_id": repository_id,
            "repository_type": repository_type,
            "items_synced": items_synced,
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="repository.sync_completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # SECURITY ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def security_alert(
        runtime_id: str = "security_engine",
        alert_id: str,
        alert_type: str,
        severity: str = "warning",
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a security.alert event.

        Published when a security alert is triggered.

        Args:
            runtime_id: ID of the security engine runtime.
            alert_id: ID of the alert.
            alert_type: Type of the alert.
            severity: Alert severity (info, warning, error, critical).
            message: Alert message.
            details: Alert details.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "details": details or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="security.alert",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def security_violation(
        runtime_id: str = "security_engine",
        violation_id: str,
        violation_type: str,
        severity: str = "error",
        message: str = "",
        source: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a security.violation event.

        Published when a security violation occurs.

        Args:
            runtime_id: ID of the security engine runtime.
            violation_id: ID of the violation.
            violation_type: Type of the violation.
            severity: Violation severity.
            message: Violation message.
            source: Source of the violation.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "violation_id": violation_id,
            "violation_type": violation_type,
            "severity": severity,
            "message": message,
            "source": source,
            **kwargs,
        }
        return SystemEvent(
            event_type="security.violation",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def security_authentication_success(
        runtime_id: str = "security_engine",
        user_id: Optional[str] = None,
        method: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a security.authentication_success event.

        Published when authentication succeeds.

        Args:
            runtime_id: ID of the security engine runtime.
            user_id: ID of the authenticated user.
            method: Authentication method.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "user_id": user_id,
            "method": method,
            **kwargs,
        }
        return SystemEvent(
            event_type="security.authentication_success",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def security_authentication_failed(
        runtime_id: str = "security_engine",
        user_id: Optional[str] = None,
        method: str = "unknown",
        reason: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a security.authentication_failed event.

        Published when authentication fails.

        Args:
            runtime_id: ID of the security engine runtime.
            user_id: ID of the user that failed authentication.
            method: Authentication method.
            reason: Reason for failure.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "user_id": user_id,
            "method": method,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="security.authentication_failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # PLANNING RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def planning_started(
        runtime_id: str = "planning_runtime",
        plan_id: str,
        task: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a planning.started event.

        Published when planning starts.

        Args:
            runtime_id: ID of the planning runtime.
            plan_id: ID of the plan.
            task: Task being planned.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "plan_id": plan_id,
            "task": task,
            **kwargs,
        }
        return SystemEvent(
            event_type="planning.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def planning_finished(
        runtime_id: str = "planning_runtime",
        plan_id: str,
        task: str,
        plan: Dict[str, Any],
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a planning.finished event.

        Published when planning finishes.

        Args:
            runtime_id: ID of the planning runtime.
            plan_id: ID of the plan.
            task: Task that was planned.
            plan: The generated plan.
            duration_ms: Duration of planning in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "plan_id": plan_id,
            "task": task,
            "plan": plan,
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="planning.finished",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def planning_failed(
        runtime_id: str = "planning_runtime",
        plan_id: str,
        task: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a planning.failed event.

        Published when planning fails.

        Args:
            runtime_id: ID of the planning runtime.
            plan_id: ID of the plan.
            task: Task that was being planned.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "plan_id": plan_id,
            "task": task,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="planning.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # AUTOMATION RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def automation_started(
        runtime_id: str = "automation_runtime",
        automation_id: str,
        automation_type: str,
        trigger: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an automation.started event.

        Published when an automation starts.

        Args:
            runtime_id: ID of the automation runtime.
            automation_id: ID of the automation.
            automation_type: Type of the automation.
            trigger: What triggered the automation.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "automation_id": automation_id,
            "automation_type": automation_type,
            "trigger": trigger,
            **kwargs,
        }
        return SystemEvent(
            event_type="automation.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def automation_completed(
        runtime_id: str = "automation_runtime",
        automation_id: str,
        automation_type: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an automation.completed event.

        Published when an automation completes.

        Args:
            runtime_id: ID of the automation runtime.
            automation_id: ID of the automation.
            automation_type: Type of the automation.
            result: Result of the automation.
            duration_ms: Duration of the automation in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "automation_id": automation_id,
            "automation_type": automation_type,
            "result": result or {},
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="automation.completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def automation_failed(
        runtime_id: str = "automation_runtime",
        automation_id: str,
        automation_type: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create an automation.failed event.

        Published when an automation fails.

        Args:
            runtime_id: ID of the automation runtime.
            automation_id: ID of the automation.
            automation_type: Type of the automation.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "automation_id": automation_id,
            "automation_type": automation_type,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="automation.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # WORKSPACE ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def workspace_changed(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        operation: str = "update",
        path: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.changed event.

        Published when a workspace changes.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            operation: Type of operation (create, update, delete).
            path: Path of the changed item.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "operation": operation,
            "path": path,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.changed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workspace_created(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        name: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.created event.

        Published when a workspace is created.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            name: Name of the workspace.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "name": name,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.created",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workspace_deleted(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        name: str,
        reason: str = "user_request",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.deleted event.

        Published when a workspace is deleted.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            name: Name of the workspace.
            reason: Reason for deletion.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "name": name,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.deleted",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workspace_file_created(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        file_path: str,
        file_type: str = "file",
        size: Optional[int] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.file_created event.

        Published when a file is created in a workspace.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            file_path: Path of the file.
            file_type: Type of the file.
            size: Size of the file in bytes.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "file_path": file_path,
            "file_type": file_type,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.file_created",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workspace_file_modified(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        file_path: str,
        file_type: str = "file",
        size: Optional[int] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.file_modified event.

        Published when a file is modified in a workspace.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            file_path: Path of the file.
            file_type: Type of the file.
            size: Size of the file in bytes.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "file_path": file_path,
            "file_type": file_type,
            "size": size,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.file_modified",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def workspace_file_deleted(
        runtime_id: str = "workspace_engine",
        workspace_id: str,
        file_path: str,
        file_type: str = "file",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a workspace.file_deleted event.

        Published when a file is deleted from a workspace.

        Args:
            runtime_id: ID of the workspace engine runtime.
            workspace_id: ID of the workspace.
            file_path: Path of the file.
            file_type: Type of the file.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "workspace_id": workspace_id,
            "file_path": file_path,
            "file_type": file_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="workspace.file_deleted",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # CORE RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def core_initialized(
        runtime_id: str = "core_runtime",
        version: str = "1.0.0",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a core.initialized event.

        Published when the core runtime initializes.

        Args:
            runtime_id: ID of the core runtime.
            version: Core version.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "version": version,
            **kwargs,
        }
        return SystemEvent(
            event_type="core.initialized",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def core_ready(
        runtime_id: str = "core_runtime",
        version: str = "1.0.0",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a core.ready event.

        Published when the core runtime is ready.

        Args:
            runtime_id: ID of the core runtime.
            version: Core version.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "version": version,
            **kwargs,
        }
        return SystemEvent(
            event_type="core.ready",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # REASONING RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def reasoning_started(
        runtime_id: str = "reasoning_runtime",
        reasoning_id: str,
        task: str,
        model_id: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a reasoning.started event.

        Published when reasoning starts.

        Args:
            runtime_id: ID of the reasoning runtime.
            reasoning_id: ID of the reasoning session.
            task: Task being reasoned about.
            model_id: ID of the model being used.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reasoning_id": reasoning_id,
            "task": task,
            "model_id": model_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="reasoning.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def reasoning_step(
        runtime_id: str = "reasoning_runtime",
        reasoning_id: str,
        step_number: int,
        step_type: str,
        content: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a reasoning.step event.

        Published for each step in the reasoning process.

        Args:
            runtime_id: ID of the reasoning runtime.
            reasoning_id: ID of the reasoning session.
            step_number: Step number.
            step_type: Type of step.
            content: Content of the step.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reasoning_id": reasoning_id,
            "step_number": step_number,
            "step_type": step_type,
            "content": content,
            **kwargs,
        }
        return SystemEvent(
            event_type="reasoning.step",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def reasoning_completed(
        runtime_id: str = "reasoning_runtime",
        reasoning_id: str,
        task: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a reasoning.completed event.

        Published when reasoning completes.

        Args:
            runtime_id: ID of the reasoning runtime.
            reasoning_id: ID of the reasoning session.
            task: Task that was reasoned about.
            result: Result of the reasoning.
            duration_ms: Duration of reasoning in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reasoning_id": reasoning_id,
            "task": task,
            "result": result or {},
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="reasoning.completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def reasoning_failed(
        runtime_id: str = "reasoning_runtime",
        reasoning_id: str,
        task: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a reasoning.failed event.

        Published when reasoning fails.

        Args:
            runtime_id: ID of the reasoning runtime.
            reasoning_id: ID of the reasoning session.
            task: Task that was being reasoned about.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reasoning_id": reasoning_id,
            "task": task,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="reasoning.failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # COORDINATION EVENTS
    # =========================================================================

    @staticmethod
    def coordination_task_created(
        runtime_id: str = "coordination_runtime",
        task_id: str,
        task_type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a coordination.task_created event.

        Published when a coordination task is created.

        Args:
            runtime_id: ID of the coordination runtime.
            task_id: ID of the task.
            task_type: Type of the task.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "task_id": task_id,
            "task_type": task_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="coordination.task_created",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def coordination_task_assigned(
        runtime_id: str = "coordination_runtime",
        task_id: str,
        worker_id: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a coordination.task_assigned event.

        Published when a coordination task is assigned to a worker.

        Args:
            runtime_id: ID of the coordination runtime.
            task_id: ID of the task.
            worker_id: ID of the worker.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "task_id": task_id,
            "worker_id": worker_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="coordination.task_assigned",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def coordination_task_completed(
        runtime_id: str = "coordination_runtime",
        task_id: str,
        worker_id: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a coordination.task_completed event.

        Published when a coordination task completes.

        Args:
            runtime_id: ID of the coordination runtime.
            task_id: ID of the task.
            worker_id: ID of the worker.
            result: Result of the task.
            duration_ms: Duration of the task in milliseconds.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "task_id": task_id,
            "worker_id": worker_id,
            "result": result or {},
            "duration_ms": duration_ms,
            **kwargs,
        }
        return SystemEvent(
            event_type="coordination.task_completed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def coordination_task_failed(
        runtime_id: str = "coordination_runtime",
        task_id: str,
        worker_id: str,
        error: str,
        error_type: str = "unknown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a coordination.task_failed event.

        Published when a coordination task fails.

        Args:
            runtime_id: ID of the coordination runtime.
            task_id: ID of the task.
            worker_id: ID of the worker.
            error: Error message.
            error_type: Type of error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "task_id": task_id,
            "worker_id": worker_id,
            "error": error,
            "error_type": error_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="coordination.task_failed",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # CONTEXT ENGINE EVENTS
    # =========================================================================

    @staticmethod
    def context_created(
        runtime_id: str = "context_engine",
        context_id: str,
        context_type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a context.created event.

        Published when a context is created.

        Args:
            runtime_id: ID of the context engine runtime.
            context_id: ID of the context.
            context_type: Type of the context.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "context_id": context_id,
            "context_type": context_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="context.created",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def context_updated(
        runtime_id: str = "context_engine",
        context_id: str,
        context_type: str,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a context.updated event.

        Published when a context is updated.

        Args:
            runtime_id: ID of the context engine runtime.
            context_id: ID of the context.
            context_type: Type of the context.
            changes: Changes made to the context.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "context_id": context_id,
            "context_type": context_type,
            "changes": changes or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="context.updated",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def context_deleted(
        runtime_id: str = "context_engine",
        context_id: str,
        context_type: str,
        reason: str = "user_request",
        **kwargs,
    ) -> SystemEvent:
        """
        Create a context.deleted event.

        Published when a context is deleted.

        Args:
            runtime_id: ID of the context engine runtime.
            context_id: ID of the context.
            context_type: Type of the context.
            reason: Reason for deletion.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "context_id": context_id,
            "context_type": context_type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="context.deleted",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # DECISION RUNTIME EVENTS
    # =========================================================================

    @staticmethod
    def decision_made(
        runtime_id: str = "decision_runtime",
        decision_id: str,
        decision_type: str,
        decision: Any,
        confidence: Optional[float] = None,
        reasoning: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a decision.made event.

        Published when a decision is made.

        Args:
            runtime_id: ID of the decision runtime.
            decision_id: ID of the decision.
            decision_type: Type of the decision.
            decision: The decision that was made.
            confidence: Confidence score (0-1).
            reasoning: Reasoning behind the decision.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "decision_id": decision_id,
            "decision_type": decision_type,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            **kwargs,
        }
        return SystemEvent(
            event_type="decision.made",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # AGENT FRAMEWORK EVENTS
    # =========================================================================

    @staticmethod
    def agent_created(
        runtime_id: str = "agent_framework",
        agent_id: str,
        agent_type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an agent.created event.

        Published when an agent is created.

        Args:
            runtime_id: ID of the agent framework runtime.
            agent_id: ID of the agent.
            agent_type: Type of the agent.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="agent.created",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def agent_started(
        runtime_id: str = "agent_framework",
        agent_id: str,
        agent_type: str,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an agent.started event.

        Published when an agent starts.

        Args:
            runtime_id: ID of the agent framework runtime.
            agent_id: ID of the agent.
            agent_type: Type of the agent.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            **kwargs,
        }
        return SystemEvent(
            event_type="agent.started",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def agent_stopped(
        runtime_id: str = "agent_framework",
        agent_id: str,
        agent_type: str,
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemEvent:
        """
        Create an agent.stopped event.

        Published when an agent stops.

        Args:
            runtime_id: ID of the agent framework runtime.
            agent_id: ID of the agent.
            agent_type: Type of the agent.
            reason: Reason for stopping.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "reason": reason,
            **kwargs,
        }
        return SystemEvent(
            event_type="agent.stopped",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def agent_message_sent(
        runtime_id: str = "agent_framework",
        agent_id: str,
        message_id: str,
        message_type: str,
        recipient_id: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an agent.message_sent event.

        Published when an agent sends a message.

        Args:
            runtime_id: ID of the agent framework runtime.
            agent_id: ID of the agent.
            message_id: ID of the message.
            message_type: Type of the message.
            recipient_id: ID of the recipient.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "agent_id": agent_id,
            "message_id": message_id,
            "message_type": message_type,
            "recipient_id": recipient_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="agent.message_sent",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def agent_message_received(
        runtime_id: str = "agent_framework",
        agent_id: str,
        message_id: str,
        message_type: str,
        sender_id: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create an agent.message_received event.

        Published when an agent receives a message.

        Args:
            runtime_id: ID of the agent framework runtime.
            agent_id: ID of the agent.
            message_id: ID of the message.
            message_type: Type of the message.
            sender_id: ID of the sender.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "agent_id": agent_id,
            "message_id": message_id,
            "message_type": message_type,
            "sender_id": sender_id,
            **kwargs,
        }
        return SystemEvent(
            event_type="agent.message_received",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    # =========================================================================
    # SYSTEM EVENTS
    # =========================================================================

    @staticmethod
    def system_startup(
        runtime_id: str = "kernel_runtime",
        version: str = "1.0.0",
        components: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.startup event.

        Published when the system starts up.

        Args:
            runtime_id: ID of the runtime publishing the event.
            version: System version.
            components: List of components starting.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "version": version,
            "components": components or [],
            **kwargs,
        }
        return SystemEvent(
            event_type="system.startup",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def system_shutdown(
        runtime_id: str = "kernel_runtime",
        reason: str = "shutdown",
        components: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.shutdown event.

        Published when the system shuts down.

        Args:
            runtime_id: ID of the runtime publishing the event.
            reason: Reason for shutdown.
            components: List of components shutting down.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "reason": reason,
            "components": components or [],
            **kwargs,
        }
        return SystemEvent(
            event_type="system.shutdown",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def system_health_check(
        runtime_id: str = "kernel_runtime",
        status: str = "healthy",
        checks: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.health_check event.

        Published when a system health check is performed.

        Args:
            runtime_id: ID of the runtime publishing the event.
            status: Overall health status.
            checks: Individual health check results.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "status": status,
            "checks": checks or {},
            **kwargs,
        }
        return SystemEvent(
            event_type="system.health_check",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def system_error(
        runtime_id: str = "kernel_runtime",
        error: str,
        error_type: str = "unknown",
        severity: str = "error",
        component: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.error event.

        Published when a system error occurs.

        Args:
            runtime_id: ID of the runtime publishing the event.
            error: Error message.
            error_type: Type of error.
            severity: Error severity.
            component: Component that encountered the error.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "error": error,
            "error_type": error_type,
            "severity": severity,
            "component": component,
            **kwargs,
        }
        return SystemEvent(
            event_type="system.error",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def system_warning(
        runtime_id: str = "kernel_runtime",
        message: str,
        warning_type: str = "unknown",
        component: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.warning event.

        Published when a system warning occurs.

        Args:
            runtime_id: ID of the runtime publishing the event.
            message: Warning message.
            warning_type: Type of warning.
            component: Component that issued the warning.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "message": message,
            "warning_type": warning_type,
            "component": component,
            **kwargs,
        }
        return SystemEvent(
            event_type="system.warning",
            runtime_id=runtime_id,
            metadata=metadata,
        )

    @staticmethod
    def system_info(
        runtime_id: str = "kernel_runtime",
        message: str,
        info_type: str = "info",
        component: Optional[str] = None,
        **kwargs,
    ) -> SystemEvent:
        """
        Create a system.info event.

        Published when a system informational message is generated.

        Args:
            runtime_id: ID of the runtime publishing the event.
            message: Informational message.
            info_type: Type of information.
            component: Component that generated the information.
            **kwargs: Additional metadata.

        Returns:
            SystemEvent instance.
        """
        metadata = {
            "message": message,
            "info_type": info_type,
            "component": component,
            **kwargs,
        }
        return SystemEvent(
            event_type="system.info",
            runtime_id=runtime_id,
            metadata=metadata,
        )
