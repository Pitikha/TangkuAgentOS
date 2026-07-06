from tangku_agentos.coding_platform import (
    CodeGraphManager,
    CodeIndexManager,
    CodeIntelligenceManager,
    SearchManager,
    StaticAnalysisManager,
    SymbolManager,
)


def test_code_intelligence_smoke() -> None:
    manager = CodeIntelligenceManager()
    index_manager = CodeIndexManager()
    symbol_manager = SymbolManager()
    graph_manager = CodeGraphManager()
    analysis_manager = StaticAnalysisManager()
    search_manager = SearchManager()

    index_manager.index_project("demo-project", files=["src/app.py", "src/utils.py"])
    symbol_manager.register_symbol("func", "app.main", kind="function")
    graph_manager.add_dependency("src/app.py", "src/utils.py")
    analysis_manager.add_analysis("demo-project", {"files": 2, "complexity": 3})
    search_manager.index_search_term("app.main")

    snapshot = manager.snapshot()
    assert snapshot["indices"]["demo-project"]["files"] == 2
    assert snapshot["symbols"]["app.main"]["kind"] == "function"
    assert snapshot["graph"]["dependencies"][0] == ("src/app.py", "src/utils.py")
    assert snapshot["analysis"]["demo-project"]["files"] == 2
    assert snapshot["search"][0] == "app.main"

    print("code intelligence checks passed")
