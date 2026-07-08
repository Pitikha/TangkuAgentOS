"""
Kernel Runtime - Runtime Communication Framework Integration

This package provides the integration of the Kernel Runtime with the
Runtime Communication Framework, making it the orchestrator of all
runtime communication in TangkuAgentOS.

The KernelManager is responsible for:
- Initializing the Runtime Communication Framework
- Registering all runtimes
- Monitoring runtime health
- Managing runtime lifecycle
- Publishing system events
- Collecting communication metrics
- Performing graceful shutdown

Example usage:
    from tangku_agentos.kernel_runtime.integration import KernelCommunicator
    
    kernel = KernelCommunicator()
    await kernel.initialize()
    await kernel.start_all_runtimes()
"""

from tangku_agentos.kernel_runtime.integration.kernel_communicator import KernelCommunicator
from tangku_agentos.kernel_runtime.integration.kernel_manager import KernelRuntimeManager
from tangku_agentos.kernel_runtime.integration.runtime_orchestrator import RuntimeOrchestrator

__all__ = [
    "KernelCommunicator",
    "KernelRuntimeManager",
    "RuntimeOrchestrator",
]
