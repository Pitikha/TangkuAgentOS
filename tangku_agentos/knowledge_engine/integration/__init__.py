"""
Knowledge Engine - Runtime Communication Framework Integration

This package provides the full integration of the Knowledge Engine with the
Runtime Communication Framework.

The Knowledge Engine provides:
- Knowledge document indexing and search
- Semantic search capabilities
- Knowledge graph management
- Integration with memory engine
- Event publishing for knowledge changes
- Health monitoring

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
