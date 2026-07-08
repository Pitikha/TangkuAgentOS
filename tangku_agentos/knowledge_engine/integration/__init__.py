"""
Knowledge Engine - Runtime Communication Framework Integration

This package provides the integration of the Knowledge Engine with the
Runtime Communication Framework.

The Knowledge Engine provides:
- Knowledge indexing and search
- Document management
- Semantic search
- Knowledge graph
- Integration with memory engine

Example usage:
    from tangku_agentos.knowledge_engine.integration import KnowledgeEngineRuntime
    from tangku_agentos.runtime_communication.integration import create_runtime_config
    
    config = create_runtime_config(
        runtime_id="knowledge_engine",
        name="Knowledge Engine",
        version="1.0.0",
        description="Manages knowledge indexing and retrieval",
        capabilities={"knowledge", "search", "indexing", "semantic"},
    )
    
    knowledge_runtime = KnowledgeEngineRuntime(config)
    await knowledge_runtime.initialize()
    await knowledge_runtime.start()
"""

from tangku_agentos.knowledge_engine.integration.knowledge_runtime import KnowledgeEngineRuntime

__all__ = ["KnowledgeEngineRuntime"]
