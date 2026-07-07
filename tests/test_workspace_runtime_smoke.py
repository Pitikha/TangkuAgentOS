from __future__ import annotations

from pathlib import Path

from tangku_agentos.configuration.manager import ConfigurationManager
from tangku_agentos.configuration.models import Configuration
from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.observability.events import EventRecorder
from tangku_agentos.security_engine.manager import SecurityManager
from tangku_agentos.workspace_engine.manager import WorkspaceManager
from tangku_agentos.workspace_engine.models import Workspace, WorkspaceConfiguration, WorkspaceMetadata
from tangku_agentos.workspace_engine.registry import WorkspaceRegistry


def test_workspace_manager_supports_real_filesystem_workflow(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    security_manager = SecurityManager()
    configuration_manager = ConfigurationManager()
    observability_manager = type("Obs", (), {"event_recorder": EventRecorder()})()
    event_bus = EventBus()
    manager = WorkspaceManager(
        registry=registry,
        security_manager=security_manager,
        configuration_manager=configuration_manager,
        observability_manager=observability_manager,
        event_bus=event_bus,
    )

    workspace = Workspace(
        workspace_id="ws-1",
        name="demo",
        root_path=str(tmp_path / "workspace"),
        metadata=WorkspaceMetadata(workspace_id="ws-1", name="demo", root_path=str(tmp_path / "workspace")),
    )
    created = manager.create_workspace(workspace)
    assert created.workspace_id == "ws-1"

    manager.set_configuration(
        "ws-1",
        WorkspaceConfiguration(
            watch_enabled=True,
            language_detection=True,
            framework_detection=True,
            metadata={"encoding": "utf-8", "newline": "\n", "ignored_directories": [".git", "__pycache__"], "ignored_files": [".DS_Store"], "workspace_limits": {"max_files": 10000}},
        ),
    )
    configuration_manager.register(Configuration(config_id="ws-1", settings={"encoding": "utf-8"}))

    manager.create_file("ws-1", "src/app.py", "print('hello')\n")
    manager.create_directory("ws-1", "docs")
    manager.append_file("ws-1", "src/app.py", "# appended\n")
    contents = manager.read_file("ws-1", "src/app.py")
    assert "hello" in contents
    assert "appended" in contents

    manager.rename_file("ws-1", "src/app.py", "src/main.py")
    assert (tmp_path / "workspace" / "src" / "main.py").exists()

    manager.copy_file("ws-1", "src/main.py", "src/main_copy.py")
    assert (tmp_path / "workspace" / "src" / "main_copy.py").exists()

    matches = manager.search("ws-1", "*.py", recursive=True)
    assert any(path.name == "main.py" for path in matches)

    opened = manager.open_workspace("ws-1")
    assert opened.workspace_id == "ws-1"
    assert manager.get_session("ws-1")["active"] is True

    status = manager.get_health("ws-1")
    assert status["status"] == "healthy"
    stats = manager.get_statistics("ws-1")
    assert stats.metadata["operations"] >= 1

    history = event_bus.history()
    assert len(history) >= 1

    manager.close_workspace("ws-1")
    assert manager.get_session("ws-1")["active"] is False

    manager.delete_workspace("ws-1")
    assert manager.get_workspace("ws-1") is None


def test_workspace_manager_detects_git_repository_and_uses_runtime_metadata(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    manager = WorkspaceManager(registry=registry)
    workspace = Workspace(
        workspace_id="ws-git",
        name="git-demo",
        root_path=str(tmp_path / "git-workspace"),
        metadata=WorkspaceMetadata(workspace_id="ws-git", name="git-demo", root_path=str(tmp_path / "git-workspace")),
    )
    manager.create_workspace(workspace)

    git_repo = tmp_path / "git-workspace"
    git_repo.mkdir(parents=True, exist_ok=True)
    git_manager = manager._git_manager
    git_manager.init_repository(str(git_repo), repository_id="ws-git")
    (git_repo / "README.md").write_text("hello\n", encoding="utf-8")
    git_manager.add(str(git_repo), ["README.md"], repository_id="ws-git")
    git_manager.commit(str(git_repo), "Initial commit", repository_id="ws-git")

    metadata = manager._repo_metadata(workspace)
    assert metadata["is_git_repo"] is True
    assert metadata["branch"] == "main"
