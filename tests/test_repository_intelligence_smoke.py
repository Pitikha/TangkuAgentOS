from __future__ import annotations

from tangku_agentos.repository_intelligence import (
    BranchManager,
    ChangeManager,
    CollaborationManager,
    CommitManager,
    DiffManager,
    GitManager,
    MergeManager,
    RepositoryManager,
    RepositoryMetadata,
    RepositoryRegistry,
    RepositoryType,
    VersionControlManager,
)


def test_repository_intelligence_smoke() -> None:
    registry = RepositoryRegistry()
    repo_manager = RepositoryManager(registry)
    repo = repo_manager.register_repository(
        "repo-1",
        RepositoryMetadata(name="demo-repo", repository_type=RepositoryType.GIT, default_branch="main"),
    )

    assert repo.repository_id == "repo-1"
    assert repo_manager.get_repository("repo-1").metadata.name == "demo-repo"

    version_control = VersionControlManager()
    session = version_control.open_repository("repo-1")
    assert session.repository_id == "repo-1"

    branch_manager = BranchManager()
    branch_manager.create_branch("repo-1", "feature/demo")
    assert branch_manager.get_branch("repo-1", "feature/demo").name == "feature/demo"

    commit_manager = CommitManager()
    commit = commit_manager.create_commit("repo-1", "Initial commit", author="agent")
    assert commit.repository_id == "repo-1"

    change_manager = ChangeManager()
    change = change_manager.track_change("repo-1", "file.py", kind="file")
    assert change.repository_id == "repo-1"

    diff_manager = DiffManager()
    diff = diff_manager.create_diff("repo-1", "file.py")
    assert diff.repository_id == "repo-1"

    merge_manager = MergeManager()
    merge_plan = merge_manager.plan_merge("repo-1", "main", "feature/demo")
    assert merge_plan["repository_id"] == "repo-1"

    collaboration_manager = CollaborationManager()
    review = collaboration_manager.start_review("repo-1", "feature/demo")
    assert review.repository_id == "repo-1"


def test_git_backend_supports_core_repository_workflow(tmp_path) -> None:
    git_manager = GitManager()
    repository_path = tmp_path / "demo-repo"
    repository_path.mkdir()

    init_result = git_manager.init_repository(str(repository_path), repository_id="demo-repo")
    assert init_result.success

    (repository_path / "README.md").write_text("hello\n", encoding="utf-8")
    add_result = git_manager.add(str(repository_path), ["README.md"], repository_id="demo-repo")
    assert add_result.success

    commit = git_manager.commit(str(repository_path), "Initial commit", repository_id="demo-repo")
    assert commit.commit_id
    assert commit.message == "Initial commit"

    status = git_manager.status(str(repository_path), repository_id="demo-repo")
    assert status.branch == "main"
    assert status.is_dirty is False

    diff = git_manager.diff(str(repository_path), repository_id="demo-repo")
    assert diff.patch == ""

    history = git_manager.log(str(repository_path), repository_id="demo-repo", max_count=5)
    assert len(history) == 1

    tag_result = git_manager.create_tag(str(repository_path), "v1.0.0", repository_id="demo-repo")
    assert tag_result.success

    metadata = git_manager.get_metadata(str(repository_path), repository_id="demo-repo")
    assert metadata.name == "demo-repo"
    assert metadata.repository_type.name == "GIT"


def test_git_backend_supports_branching_and_clone_workflow(tmp_path) -> None:
    git_manager = GitManager()

    remote_path = tmp_path / "remote.git"
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    init_result = git_manager.init_repository(str(source_repo), repository_id="source")
    assert init_result.success

    (source_repo / "app.txt").write_text("base\n", encoding="utf-8")
    git_manager.add(str(source_repo), ["app.txt"], repository_id="source")
    git_manager.commit(str(source_repo), "Initial source commit", repository_id="source")

    git_manager.init_repository(str(remote_path), repository_id="remote", bare=True)
    git_manager.push(str(source_repo), str(remote_path), repository_id="source")

    clone_result = git_manager.clone_repository(str(remote_path), str(tmp_path / "clone"), repository_id="clone")
    assert clone_result.success

    branch = git_manager.create_branch(str(tmp_path / "clone"), "feature/test", repository_id="clone", checkout=True)
    assert branch.name == "feature/test"

    status = git_manager.status(str(tmp_path / "clone"), repository_id="clone")
    assert status.branch == "feature/test"

    health = git_manager.get_health(str(tmp_path / "clone"), repository_id="clone")
    assert health.status == "healthy"
