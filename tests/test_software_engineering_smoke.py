from __future__ import annotations

from tangku_agentos.software_engineering_intelligence import (
    ArchitectureManager,
    BugFixManager,
    CodeGenerationManager,
    EngineeringSessionManager,
    FeatureDevelopmentManager,
    PatternLibrary,
    ProjectAnalyzer,
    SoftwareEngineeringManager,
)


def test_software_engineering_platform_smoke() -> None:
    engineering = SoftwareEngineeringManager()
    session_id = engineering.start_session("demo-project")
    engineering.update_context(session_id, {"goal": "build autonomous engineering workflows"})

    plan_id = engineering.plan_work("Implement engineering platform", metadata={"scope": "core"})
    assert plan_id is not None

    session_manager = EngineeringSessionManager()
    assert session_manager.create_session("demo-project") is not None

    arch = ArchitectureManager()
    arch.record_snapshot("core", {"layers": ["domain", "runtime"]})
    assert arch.get_latest_snapshot("core") is not None

    generator = CodeGenerationManager()
    request = generator.create_request("feature", "Create a manager for engineering sessions")
    assert request["kind"] == "feature"

    analyzer = ProjectAnalyzer()
    analysis = analyzer.analyze_project({"files": ["src/main.py", "tests/test_main.py"]})
    assert analysis["summary"]["file_count"] == 2

    feature_manager = FeatureDevelopmentManager()
    feature = feature_manager.start_feature("autonomous-review")
    assert feature["feature_id"] == "autonomous-review"

    bug_manager = BugFixManager()
    bug = bug_manager.start_bug_fix("repair-workflow")
    assert bug["bug_id"] == "repair-workflow"

    library = PatternLibrary()
    library.register_pattern("manager", {"name": "manager"})
    assert library.get_pattern("manager") is not None
