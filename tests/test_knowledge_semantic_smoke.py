from tangku_agentos.knowledge_engine import (
    CitationManager,
    ContextAssemblyManager,
    DocumentManager,
    KnowledgeGraphManager,
    KnowledgeSyncManager,
    RetrievalManager,
    SemanticIndexManager,
)


def test_knowledge_semantic_smoke() -> None:
    graph_manager = KnowledgeGraphManager()
    semantic_index = SemanticIndexManager()
    retrieval_manager = RetrievalManager()
    document_manager = DocumentManager()
    context_manager = ContextAssemblyManager()
    citation_manager = CitationManager()
    sync_manager = KnowledgeSyncManager()

    graph_manager.add_node("doc-1", "document")
    graph_manager.add_edge("doc-1", "doc-2", "related")
    semantic_index.index_document("doc-1", {"title": "Architecture"})
    retrieval_manager.add_source("workspace", {"scope": "project"})
    document_manager.register_document("doc-1", {"title": "Architecture"})
    context_manager.add_context("workspace", {"scope": "project"})
    citation_manager.add_citation("doc-1", {"source": "workspace"})
    sync_manager.sync("workspace", {"status": "ok"})

    assert graph_manager.snapshot()["nodes"]["doc-1"]["label"] == "document"
    assert semantic_index.snapshot()["doc-1"]["metadata"]["title"] == "Architecture"
    assert retrieval_manager.snapshot()["sources"][0][0] == "workspace"
    assert document_manager.snapshot()["doc-1"]["metadata"]["title"] == "Architecture"
    assert context_manager.snapshot()["workspace"]["scope"] == "project"
    assert citation_manager.snapshot()["doc-1"]["source"] == "workspace"
    assert sync_manager.snapshot()["workspace"]["status"] == "ok"

    print("knowledge semantic checks passed")
