"""
Runtime Communication Framework - Standard System Commands

This module defines all standard system commands for TangkuAgentOS.
These commands are used for system-level operations between runtimes.

Command Naming Convention:
- Runtime commands: StartRuntime, StopRuntime, RestartRuntime, etc.
- Model commands: LoadModel, UnloadModel, etc.
- Workflow commands: ExecuteWorkflow, PauseWorkflow, etc.
- Provider commands: ConnectProvider, DisconnectProvider, etc.
- Memory commands: SaveMemory, LoadMemory, etc.
- Knowledge commands: SearchKnowledge, IndexKnowledge, etc.
- Terminal commands: ExecuteTerminalCommand, etc.
- Repository commands: SyncRepository, IndexRepository, etc.
- Security commands: Authenticate, Authorize, etc.
- Planning commands: CreatePlan, ExecutePlan, etc.
- Automation commands: RunAutomation, StopAutomation, etc.

All commands follow the pattern:
- Command name: PascalCase (e.g., StartRuntime)
- Command type: lowercase with dots (e.g., "runtime.start")
- Parameters: Dictionary with command-specific parameters

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Command, MessageType


@dataclass
class SystemCommand:
    """
    Base class for all system commands.

    Attributes:
        command_type: Type of the command (e.g., "runtime.start").
        target_runtime_id: ID of the runtime to send the command to.
        sender_id: ID of the runtime sending the command.
        parameters: Command parameters.
        timeout: Timeout in seconds.
        priority: Command priority.
        correlation_id: Correlation ID for tracing.
        metadata: Additional command metadata.
    """

    command_type: str
    target_runtime_id: Optional[str] = None
    sender_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: str = "normal"
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_command(self) -> "Command":
        """
        Convert to a Command message.

        Returns:
            Command message.
        """
        from tangku_agentos.runtime_communication import Command, MessageType

        return Command(
            message_type=MessageType.COMMAND,
            sender_id=self.sender_id,
            recipient_id=self.target_runtime_id,
            command_type=self.command_type,
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
            "command_type": self.command_type,
            "target_runtime_id": self.target_runtime_id,
            "sender_id": self.sender_id,
            "parameters": self.parameters,
            "timeout": self.timeout,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemCommand":
        """
        Create from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            SystemCommand instance.
        """
        return cls(
            command_type=data.get("command_type", ""),
            target_runtime_id=data.get("target_runtime_id"),
            sender_id=data.get("sender_id", ""),
            parameters=data.get("parameters", {}),
            timeout=data.get("timeout", 30.0),
            priority=data.get("priority", "normal"),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            metadata={k: v for k, v in data.items() if k not in (
                "command_type", "target_runtime_id", "sender_id",
                "parameters", "timeout", "priority", "correlation_id"
            )},
        )


class SystemCommands:
    """
    Factory class for creating standard system commands.

    This class provides static methods for creating all standard system commands.
    Each method returns a properly formatted SystemCommand instance.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.commands import SystemCommands
        >>> 
        >>> # Create a start runtime command
        >>> command = SystemCommands.StartRuntime(
        ...     target_runtime_id="memory_runtime",
        ...     sender_id="kernel_runtime"
        ... )
        >>> 
        >>> # Send the command
        >>> await command_bus.send(command.to_command())
    """

    # =========================================================================
    # RUNTIME COMMANDS
    # =========================================================================

    @staticmethod
    def StartRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.start command.

        Args:
            target_runtime_id: ID of the runtime to start.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.start",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StopRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        force: bool = False,
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.stop command.

        Args:
            target_runtime_id: ID of the runtime to stop.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            force: Whether to force stop.
            reason: Reason for stopping.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.stop",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"force": force, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def RestartRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 120.0,
        priority: str = "high",
        reason: str = "restart",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.restart command.

        Args:
            target_runtime_id: ID of the runtime to restart.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for restarting.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.restart",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def PauseRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        reason: str = "manual",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.pause command.

        Args:
            target_runtime_id: ID of the runtime to pause.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for pausing.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.pause",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ResumeRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        reason: str = "manual",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.resume command.

        Args:
            target_runtime_id: ID of the runtime to resume.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for resuming.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.resume",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ReloadRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "normal",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.reload command.

        Args:
            target_runtime_id: ID of the runtime to reload.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            config: New configuration for the runtime.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.reload",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"config": config or {}, **kwargs},
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
    ) -> SystemCommand:
        """
        Create a runtime.get_status command.

        Args:
            target_runtime_id: ID of the runtime to check.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def RegisterRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "high",
        name: str = "",
        type: str = "",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.register command.

        Args:
            target_runtime_id: ID of the runtime to register.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            name: Human-readable name.
            type: Runtime type.
            version: Runtime version.
            capabilities: List of capabilities.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.register",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "name": name,
                "type": type,
                "version": version,
                "capabilities": capabilities or [],
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def UnregisterRuntime(
        target_runtime_id: str,
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "high",
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a runtime.unregister command.

        Args:
            target_runtime_id: ID of the runtime to unregister.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for unregistration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="runtime.unregister",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # MODEL COMMANDS
    # =========================================================================

    @staticmethod
    def LoadModel(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 120.0,
        priority: str = "high",
        model_id: str = "",
        model_name: str = "",
        model_type: str = "",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a model.load command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            model_id: ID of the model to load.
            model_name: Name of the model.
            model_type: Type of the model.
            config: Model configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.load",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "model_id": model_id,
                "model_name": model_name,
                "model_type": model_type,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def UnloadModel(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "normal",
        model_id: str = "",
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a model.unload command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            model_id: ID of the model to unload.
            reason: Reason for unloading.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.unload",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"model_id": model_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def RunInference(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        model_id: str = "",
        prompt: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a model.run_inference command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            model_id: ID of the model to use.
            prompt: Input prompt for inference.
            parameters: Inference parameters.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.run_inference",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "model_id": model_id,
                "prompt": prompt,
                "parameters": parameters or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def CancelInference(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "high",
        inference_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a model.cancel_inference command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            inference_id: ID of the inference to cancel.
            reason: Reason for cancellation.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.cancel_inference",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"inference_id": inference_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListModels(
        target_runtime_id: str = "model_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a model.list command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for models.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.list",
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
    ) -> SystemCommand:
        """
        Create a model.get_info command.

        Args:
            target_runtime_id: ID of the model runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            model_id: ID of the model to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="model.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"model_id": model_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # WORKFLOW COMMANDS
    # =========================================================================

    @staticmethod
    def ExecuteWorkflow(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 300.0,
        priority: str = "high",
        workflow_id: str = "",
        workflow_type: str = "",
        input_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.execute command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workflow_id: ID of the workflow to execute.
            workflow_type: Type of the workflow.
            input_data: Input data for the workflow.
            config: Workflow configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.execute",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "input_data": input_data or {},
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def PauseWorkflow(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workflow_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.pause command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workflow_id: ID of the workflow to pause.
            reason: Reason for pausing.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.pause",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ResumeWorkflow(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workflow_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.resume command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workflow_id: ID of the workflow to resume.
            reason: Reason for resuming.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.resume",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def CancelWorkflow(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workflow_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.cancel command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workflow_id: ID of the workflow to cancel.
            reason: Reason for cancellation.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.cancel",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workflow_id": workflow_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetWorkflowStatus(
        target_runtime_id: str = "workflow_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        workflow_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.get_status command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workflow_id: ID of the workflow to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.get_status",
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
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workflow.list command.

        Args:
            target_runtime_id: ID of the workflow engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for workflows.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workflow.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # PROVIDER COMMANDS
    # =========================================================================

    @staticmethod
    def ConnectProvider(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        provider_id: str = "",
        provider_type: str = "",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a provider.connect command.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            provider_id: ID of the provider to connect.
            provider_type: Type of the provider.
            config: Provider configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="provider.connect",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "provider_id": provider_id,
                "provider_type": provider_type,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DisconnectProvider(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        provider_id: str = "",
        reason: str = "shutdown",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a provider.disconnect command.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            provider_id: ID of the provider to disconnect.
            reason: Reason for disconnection.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="provider.disconnect",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def TestProvider(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        provider_id: str = "",
        test_type: str = "connectivity",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a provider.test command.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            provider_id: ID of the provider to test.
            test_type: Type of test to perform.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="provider.test",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, "test_type": test_type, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ListProviders(
        target_runtime_id: str = "provider_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a provider.list command.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for providers.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="provider.list",
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
    ) -> SystemCommand:
        """
        Create a provider.get_status command.

        Args:
            target_runtime_id: ID of the provider runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            provider_id: ID of the provider to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="provider.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"provider_id": provider_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # MEMORY COMMANDS
    # =========================================================================

    @staticmethod
    def SaveMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        memory_id: str = "",
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a memory.save command.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            memory_id: ID of the memory to save.
            data: Data to save.
            metadata: Memory metadata.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="memory.save",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "memory_id": memory_id,
                "data": data or {},
                "metadata": metadata or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def LoadMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        memory_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a memory.load command.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            memory_id: ID of the memory to load.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="memory.load",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"memory_id": memory_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        memory_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a memory.delete command.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            memory_id: ID of the memory to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="memory.delete",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"memory_id": memory_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SearchMemory(
        target_runtime_id: str = "memory_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a memory.search command.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="memory.search",
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
        **kwargs,
    ) -> SystemCommand:
        """
        Create a memory.list command.

        Args:
            target_runtime_id: ID of the memory engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for memories.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="memory.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # KNOWLEDGE COMMANDS
    # =========================================================================

    @staticmethod
    def SearchKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a knowledge.search command.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="knowledge.search",
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
    def IndexKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "normal",
        document_id: str = "",
        content: str = "",
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a knowledge.index command.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            document_id: ID of the document to index.
            content: Content to index.
            source: Source of the document.
            metadata: Document metadata.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="knowledge.index",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "document_id": document_id,
                "content": content,
                "source": source,
                "metadata": metadata or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        document_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a knowledge.delete command.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            document_id: ID of the document to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="knowledge.delete",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"document_id": document_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SyncKnowledge(
        target_runtime_id: str = "knowledge_engine",
        sender_id: str = "",
        timeout: float = 120.0,
        priority: str = "normal",
        source: str = "",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a knowledge.sync command.

        Args:
            target_runtime_id: ID of the knowledge engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            source: Source to sync from.
            config: Sync configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="knowledge.sync",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"source": source, "config": config or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # TERMINAL COMMANDS
    # =========================================================================

    @staticmethod
    def ExecuteTerminalCommand(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "normal",
        command: str = "",
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_command: Optional[float] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a terminal.execute_command command.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            command: Command to execute.
            cwd: Working directory.
            env: Environment variables.
            timeout_command: Timeout for the command itself.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="terminal.execute_command",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "command": command,
                "cwd": cwd,
                "env": env or {},
                "timeout": timeout_command,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StartTerminalSession(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        session_id: str = "",
        shell: str = "/bin/bash",
        cwd: Optional[str] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a terminal.start_session command.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            session_id: ID of the session.
            shell: Shell to use.
            cwd: Working directory.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="terminal.start_session",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "session_id": session_id,
                "shell": shell,
                "cwd": cwd,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def EndTerminalSession(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        session_id: str = "",
        reason: str = "exit",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a terminal.end_session command.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            session_id: ID of the session to end.
            reason: Reason for ending.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="terminal.end_session",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"session_id": session_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SendTerminalInput(
        target_runtime_id: str = "terminal_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        session_id: str = "",
        input_data: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a terminal.send_input command.

        Args:
            target_runtime_id: ID of the terminal runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            session_id: ID of the session.
            input_data: Input to send.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="terminal.send_input",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"session_id": session_id, "input": input_data, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # REPOSITORY COMMANDS
    # =========================================================================

    @staticmethod
    def SyncRepository(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 300.0,
        priority: str = "normal",
        repository_id: str = "",
        repository_url: str = "",
        repository_type: str = "git",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a repository.sync command.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            repository_id: ID of the repository.
            repository_url: URL of the repository.
            repository_type: Type of the repository.
            config: Sync configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="repository.sync",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "repository_id": repository_id,
                "repository_url": repository_url,
                "repository_type": repository_type,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def IndexRepository(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 300.0,
        priority: str = "normal",
        repository_id: str = "",
        repository_url: str = "",
        repository_type: str = "git",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a repository.index command.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            repository_id: ID of the repository.
            repository_url: URL of the repository.
            repository_type: Type of the repository.
            config: Index configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="repository.index",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "repository_id": repository_id,
                "repository_url": repository_url,
                "repository_type": repository_type,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SearchRepository(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        repository_id: str = "",
        query: str = "",
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a repository.search command.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            repository_id: ID of the repository to search.
            query: Search query.
            filter: Filter criteria.
            limit: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="repository.search",
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
    def ListRepositories(
        target_runtime_id: str = "repository_intelligence",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a repository.list command.

        Args:
            target_runtime_id: ID of the repository intelligence runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for repositories.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="repository.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # SECURITY COMMANDS
    # =========================================================================

    @staticmethod
    def Authenticate(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "high",
        user_id: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
        method: str = "token",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a security.authenticate command.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            user_id: ID of the user to authenticate.
            credentials: Authentication credentials.
            method: Authentication method.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="security.authenticate",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "user_id": user_id,
                "credentials": credentials or {},
                "method": method,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def Authorize(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "high",
        user_id: Optional[str] = None,
        action: str = "",
        resource: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a security.authorize command.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            user_id: ID of the user to authorize.
            action: Action to authorize.
            resource: Resource to access.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="security.authorize",
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
    def CheckPermission(
        target_runtime_id: str = "security_engine",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        user_id: Optional[str] = None,
        permission: str = "",
        resource: Optional[str] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a security.check_permission command.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            user_id: ID of the user to check.
            permission: Permission to check.
            resource: Resource to check permission for.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="security.check_permission",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "user_id": user_id,
                "permission": permission,
                "resource": resource,
                **kwargs,
            },
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
    ) -> SystemCommand:
        """
        Create a security.get_user_info command.

        Args:
            target_runtime_id: ID of the security engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            user_id: ID of the user to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="security.get_user_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"user_id": user_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # PLANNING COMMANDS
    # =========================================================================

    @staticmethod
    def CreatePlan(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        task: str = "",
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a planning.create_plan command.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task: Task to plan.
            context: Context for planning.
            constraints: List of constraints.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="planning.create_plan",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "task": task,
                "context": context or {},
                "constraints": constraints or [],
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ExecutePlan(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 300.0,
        priority: str = "high",
        plan_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a planning.execute_plan command.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            plan_id: ID of the plan to execute.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="planning.execute_plan",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def CancelPlan(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        plan_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a planning.cancel_plan command.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            plan_id: ID of the plan to cancel.
            reason: Reason for cancellation.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="planning.cancel_plan",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetPlanStatus(
        target_runtime_id: str = "planning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        plan_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a planning.get_plan_status command.

        Args:
            target_runtime_id: ID of the planning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            plan_id: ID of the plan to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="planning.get_plan_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"plan_id": plan_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # AUTOMATION COMMANDS
    # =========================================================================

    @staticmethod
    def RunAutomation(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 300.0,
        priority: str = "high",
        automation_id: str = "",
        automation_type: str = "",
        trigger: str = "manual",
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create an automation.run command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            automation_id: ID of the automation to run.
            automation_type: Type of the automation.
            trigger: What triggered the automation.
            input_data: Input data for the automation.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.run",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "automation_id": automation_id,
                "automation_type": automation_type,
                "trigger": trigger,
                "input_data": input_data or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StopAutomation(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        automation_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an automation.stop command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            automation_id: ID of the automation to stop.
            reason: Reason for stopping.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.stop",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def PauseAutomation(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        automation_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an automation.pause command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            automation_id: ID of the automation to pause.
            reason: Reason for pausing.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.pause",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def ResumeAutomation(
        target_runtime_id: str = "automation_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        automation_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an automation.resume command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            automation_id: ID of the automation to resume.
            reason: Reason for resuming.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.resume",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, "reason": reason, **kwargs},
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
    ) -> SystemCommand:
        """
        Create an automation.get_status command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            automation_id: ID of the automation to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"automation_id": automation_id, **kwargs},
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
        **kwargs,
    ) -> SystemCommand:
        """
        Create an automation.list command.

        Args:
            target_runtime_id: ID of the automation runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for automations.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="automation.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # WORKSPACE COMMANDS
    # =========================================================================

    @staticmethod
    def CreateWorkspace(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workspace_id: str = "",
        name: str = "",
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.create command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace to create.
            name: Name of the workspace.
            description: Description of the workspace.
            config: Workspace configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.create",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "name": name,
                "description": description,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteWorkspace(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workspace_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.delete command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.delete",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workspace_id": workspace_id, "reason": reason, **kwargs},
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
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.list command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            filter: Filter criteria for workspaces.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
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
    ) -> SystemCommand:
        """
        Create a workspace.get_info command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace to get info for.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.get_info",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"workspace_id": workspace_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def OpenFile(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workspace_id: str = "",
        file_path: str = "",
        mode: str = "read",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.open_file command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace.
            file_path: Path of the file to open.
            mode: Mode to open the file (read, write, append).
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.open_file",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "file_path": file_path,
                "mode": mode,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SaveFile(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workspace_id: str = "",
        file_path: str = "",
        content: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.save_file command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace.
            file_path: Path of the file to save.
            content: Content to save.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.save_file",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "file_path": file_path,
                "content": content,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteFile(
        target_runtime_id: str = "workspace_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        workspace_id: str = "",
        file_path: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a workspace.delete_file command.

        Args:
            target_runtime_id: ID of the workspace engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            workspace_id: ID of the workspace.
            file_path: Path of the file to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="workspace.delete_file",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "workspace_id": workspace_id,
                "file_path": file_path,
                "reason": reason,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # REASONING COMMANDS
    # =========================================================================

    @staticmethod
    def StartReasoning(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 120.0,
        priority: str = "high",
        task: str = "",
        context: Optional[Dict[str, Any]] = None,
        model_id: Optional[str] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a reasoning.start command.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task: Task to reason about.
            context: Context for reasoning.
            model_id: ID of the model to use.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="reasoning.start",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "task": task,
                "context": context or {},
                "model_id": model_id,
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StopReasoning(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        reasoning_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a reasoning.stop command.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reasoning_id: ID of the reasoning session to stop.
            reason: Reason for stopping.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="reasoning.stop",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reasoning_id": reasoning_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetReasoningState(
        target_runtime_id: str = "reasoning_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        reasoning_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a reasoning.get_state command.

        Args:
            target_runtime_id: ID of the reasoning runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reasoning_id: ID of the reasoning session to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="reasoning.get_state",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reasoning_id": reasoning_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # COORDINATION COMMANDS
    # =========================================================================

    @staticmethod
    def CreateTask(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        task_id: str = "",
        task_type: str = "",
        payload: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a coordination.create_task command.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task_id: ID of the task to create.
            task_type: Type of the task.
            payload: Task payload.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="coordination.create_task",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "task_id": task_id,
                "task_type": task_type,
                "payload": payload or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def AssignTask(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        task_id: str = "",
        worker_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a coordination.assign_task command.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task_id: ID of the task to assign.
            worker_id: ID of the worker to assign to.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="coordination.assign_task",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"task_id": task_id, "worker_id": worker_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def CompleteTask(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        task_id: str = "",
        result: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a coordination.complete_task command.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task_id: ID of the task to complete.
            result: Result of the task.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="coordination.complete_task",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"task_id": task_id, "result": result or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def FailTask(
        target_runtime_id: str = "coordination_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        task_id: str = "",
        error: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a coordination.fail_task command.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.\n            priority: Command priority.
            task_id: ID of the task to fail.
            error: Error message.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="coordination.fail_task",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"task_id": task_id, "error": error, **kwargs},
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
    ) -> SystemCommand:
        """
        Create a coordination.get_task_status command.

        Args:
            target_runtime_id: ID of the coordination runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            task_id: ID of the task to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="coordination.get_task_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"task_id": task_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # CONTEXT ENGINE COMMANDS
    # =========================================================================

    @staticmethod
    def CreateContext(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        context_id: str = "",
        context_type: str = "",
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a context.create command.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            context_id: ID of the context to create.
            context_type: Type of the context.
            data: Context data.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="context.create",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "context_id": context_id,
                "context_type": context_type,
                "data": data or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def UpdateContext(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        context_id: str = "",
        updates: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a context.update command.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            context_id: ID of the context to update.
            updates: Updates to apply to the context.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="context.update",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"context_id": context_id, "updates": updates or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteContext(
        target_runtime_id: str = "context_engine",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        context_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a context.delete command.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            context_id: ID of the context to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="context.delete",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"context_id": context_id, "reason": reason, **kwargs},
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
    ) -> SystemCommand:
        """
        Create a context.get command.

        Args:
            target_runtime_id: ID of the context engine.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            context_id: ID of the context to retrieve.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="context.get",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"context_id": context_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # DECISION COMMANDS
    # =========================================================================

    @staticmethod
    def MakeDecision(
        target_runtime_id: str = "decision_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        decision_type: str = "",
        options: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        criteria: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a decision.make command.

        Args:
            target_runtime_id: ID of the decision runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            decision_type: Type of decision to make.
            options: List of options to choose from.
            context: Context for the decision.
            criteria: Decision criteria.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="decision.make",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "decision_type": decision_type,
                "options": options or [],
                "context": context or {},
                "criteria": criteria or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def EvaluateOptions(
        target_runtime_id: str = "decision_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "normal",
        decision_type: str = "",
        options: Optional[List[Any]] = None,
        criteria: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a decision.evaluate_options command.

        Args:
            target_runtime_id: ID of the decision runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            decision_type: Type of decision.
            options: List of options to evaluate.
            criteria: Evaluation criteria.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="decision.evaluate_options",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "decision_type": decision_type,
                "options": options or [],
                "criteria": criteria or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # AGENT FRAMEWORK COMMANDS
    # =========================================================================

    @staticmethod
    def CreateAgent(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        agent_id: str = "",
        agent_type: str = "",
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.create command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to create.
            agent_type: Type of the agent.
            config: Agent configuration.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.create",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "agent_id": agent_id,
                "agent_type": agent_type,
                "config": config or {},
                **kwargs,
            },
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StartAgent(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "high",
        agent_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.start command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to start.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.start",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def StopAgent(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        agent_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.stop command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to stop.
            reason: Reason for stopping.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.stop",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def DeleteAgent(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        agent_id: str = "",
        reason: str = "user_request",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.delete command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to delete.
            reason: Reason for deletion.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.delete",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, "reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def SendAgentMessage(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        agent_id: str = "",
        message_type: str = "",
        content: Any = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.send_message command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to send to.
            message_type: Type of the message.
            content: Message content.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.send_message",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "agent_id": agent_id,
                "message_type": message_type,
                "content": content,
                **kwargs,
            },
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
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.list command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.\n            priority: Command priority.
            filter: Filter criteria for agents.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.list",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"filter": filter or {}, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetAgentStatus(
        target_runtime_id: str = "agent_framework",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        agent_id: str = "",
        **kwargs,
    ) -> SystemCommand:
        """
        Create an agent.get_status command.

        Args:
            target_runtime_id: ID of the agent framework.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            agent_id: ID of the agent to check.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="agent.get_status",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"agent_id": agent_id, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    # =========================================================================
    # SYSTEM COMMANDS
    # =========================================================================

    @staticmethod
    def ShutdownSystem(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 60.0,
        priority: str = "critical",
        reason: str = "shutdown",
        force: bool = False,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a system.shutdown command.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for shutdown.
            force: Whether to force shutdown.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.shutdown",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, "force": force, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def RestartSystem(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 120.0,
        priority: str = "critical",
        reason: str = "restart",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a system.restart command.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            reason: Reason for restart.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.restart",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={"reason": reason, **kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def GetSystemStatus(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 10.0,
        priority: str = "normal",
        **kwargs,
    ) -> SystemCommand:
        """
        Create a system.get_status command.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.get_status",
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
    ) -> SystemCommand:
        """
        Create a system.get_metrics command.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.get_metrics",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )

    @staticmethod
    def BroadcastMessage(
        target_runtime_id: str = "kernel_runtime",
        sender_id: str = "",
        timeout: float = 30.0,
        priority: str = "normal",
        message_type: str = "",
        message: str = "",
        channels: Optional[List[str]] = None,
        **kwargs,
    ) -> SystemCommand:
        """
        Create a system.broadcast command.

        Args:
            target_runtime_id: ID of the kernel runtime.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            message_type: Type of the message.
            message: Message content.
            channels: Channels to broadcast to.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.broadcast",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={
                "message_type": message_type,
                "message": message,
                "channels": channels or [],
                **kwargs,
            },
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
    ) -> SystemCommand:
        """
        Create a system.ping command.

        Args:
            target_runtime_id: ID of the runtime to ping.
            sender_id: ID of the runtime sending the command.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional parameters.

        Returns:
            SystemCommand instance.
        """
        return SystemCommand(
            command_type="system.ping",
            target_runtime_id=target_runtime_id,
            sender_id=sender_id,
            parameters={**kwargs},
            timeout=timeout,
            priority=priority,
        )
