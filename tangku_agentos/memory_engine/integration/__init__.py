"""
Memory Engine - Runtime Communication Framework Integration

This package provides the full integration of the Memory Engine with the
Runtime Communication Framework.

The Memory Engine is now a production-ready runtime that:
- Inherits from BaseRuntime
- Handles commands and queries through the framework
- Publishes standard system events
- Supports health monitoring
- Provides comprehensive memory management

Example usage:
    from tangku_agentos.memory_engine.integration import MemoryEngineRuntime
    from tangku_agentos.runtime_communication.integration import create_runtime_config
    
    # Create configuration
    config = create_runtime_config(
        runtime_id="memory_engine",
        name="Memory Engine",
        version="1.0.0",
        description="Manages memory storage and retrieval for TangkuAgentOS",
        capabilities={"memory", "storage", "persistence", "versioning", "tagging"},
    )
    
    # Create and start the runtime
    memory_runtime = MemoryEngineRuntime(config)
    await memory_runtime.initialize()
    await memory_runtime.start()
    
    # The runtime is now ready to handle memory operations
"""

from tangku_agentos.memory_engine.integration.memory_runtime import MemoryEngineRuntime

__all__ = ["MemoryEngineRuntime"]
