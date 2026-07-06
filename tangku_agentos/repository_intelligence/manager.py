from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Tuple

from .interfaces import (
    BranchManager as BranchManagerInterface,
    CommitManager as CommitManagerInterface,
    MergeManager as MergeManagerInterface,
    RepositoryManagerInterface,
)
from .models import (
    Branch,
    BranchLifecycle,
    BranchMetadata,
    ChangeHistory,
    ChangeMetadata,
    Commit,
    CommitGraph,
    CommitHistory,
    CommitMetadata,
    ConflictMetadata,
    DiffContext,
    DiffMetadata,
    MergeContext,
    MergeMetadata,
    PullRequest,
    Repository,
    RepositoryConfiguration,
    RepositoryContext,
    RepositoryHealth,
    RepositoryLifecycle,
    RepositoryMetadata,
    RepositoryPermissions,
    RepositorySession,
    RepositoryStatistics,
    ReviewMetadata,
    ReviewSession,
    RepositoryType,
    VersionControlMetadata,
)
from .registry import RepositoryRegistry


@dataclass(frozen=True)
class GitOperationResult:
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    repository_path: str | None = None
    command: tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GitStatus:
    repository_path: str
    branch: str
    is_dirty: bool
    stdout: str = ""
    stderr: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GitDiff:
    repository_path: str
    patch: str
    stdout: str = ""
    stderr: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GitHealth:
    repository_path: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GitMetadata:
    name: str
    repository_type: RepositoryType
    default_branch: str
    repository_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RepositoryManager(RepositoryManagerInterface):
    """Manager for repository intelligence operations."""

    def __init__(self, registry: RepositoryRegistry | None = None) -> None:
        self._registry = registry or RepositoryRegistry()
        self._repositories: Dict[str, Repository] = {}
        self._contexts: Dict[str, RepositoryContext] = {}
        self._sessions: Dict[str, RepositorySession] = {}
        self._lifecycles: Dict[str, RepositoryLifecycle] = {}
        self._configurations: Dict[str, RepositoryConfiguration] = {}
        self._statistics: Dict[str, RepositoryStatistics] = {}
        self._health: Dict[str, RepositoryHealth] = {}
        self._lock = RLock()

    def register_repository(self, repository_id: str, metadata: RepositoryMetadata) -> Repository:
        repository = Repository(repository_id=repository_id, metadata=metadata)
        with self._lock:
            self._registry.register(repository)
            self._repositories[repository_id] = repository
            self._contexts[repository_id] = RepositoryContext(repository_id=repository_id, state="registered")
            self._sessions[repository_id] = RepositorySession(repository_id=repository_id, session_id=f"session-{repository_id}")
            self._lifecycles[repository_id] = RepositoryLifecycle(repository_id=repository_id, state="registered")
            self._configurations[repository_id] = RepositoryConfiguration(repository_id=repository_id)
            self._statistics[repository_id] = RepositoryStatistics(repository_id=repository_id, stats={"branches": 0, "commits": 0})
            self._health[repository_id] = RepositoryHealth(repository_id=repository_id, status="healthy")
        return repository

    def scan_repository(self, repository_id: str) -> Repository:
        return self.get_repository(repository_id)

    def get_repository(self, repository_id: str) -> Repository:
        return self._registry.resolve(repository_id)

    def list_repositories(self) -> list[Repository]:
        return list(self._registry.list_registered())

    def open_repository(self, repository_id: str) -> RepositorySession:
        with self._lock:
            session = self._sessions.get(repository_id)
            if session is None:
                session = RepositorySession(repository_id=repository_id, session_id=f"session-{repository_id}", state="open")
                self._sessions[repository_id] = session
            self._lifecycles[repository_id] = RepositoryLifecycle(repository_id=repository_id, state="open")
            return session

    def close_repository(self, repository_id: str) -> RepositorySession:
        with self._lock:
            self._lifecycles[repository_id] = RepositoryLifecycle(repository_id=repository_id, state="closed")
            return self._sessions.get(repository_id, RepositorySession(repository_id=repository_id, session_id=f"session-{repository_id}", state="closed"))

    def get_context(self, repository_id: str) -> RepositoryContext:
        return self._contexts.get(repository_id, RepositoryContext(repository_id=repository_id))

    def get_health(self, repository_id: str) -> RepositoryHealth:
        return self._health.get(repository_id, RepositoryHealth(repository_id=repository_id))


class VersionControlManager:
    """Provider-agnostic version control runtime."""

    def __init__(self) -> None:
        self._providers: Dict[str, Any] = {}
        self._sessions: Dict[str, RepositorySession] = {}
        self._metadata: Dict[str, VersionControlMetadata] = {}
        self._lock = RLock()

    def register_provider(self, provider_id: str, provider: Any) -> None:
        with self._lock:
            self._providers[provider_id] = provider

    def initialize_repository(self, repository_id: str, provider_id: str = "abstract") -> VersionControlMetadata:
        metadata = VersionControlMetadata(repository_id=repository_id, provider=provider_id)
        with self._lock:
            self._metadata[repository_id] = metadata
        return metadata

    def clone(self, repository_id: str, provider_id: str = "abstract") -> VersionControlMetadata:
        return self.initialize_repository(repository_id, provider_id=provider_id)

    def open_repository(self, repository_id: str) -> RepositorySession:
        with self._lock:
            session = RepositorySession(repository_id=repository_id, session_id=f"vc-{repository_id}", state="open")
            self._sessions[repository_id] = session
            return session

    def close_repository(self, repository_id: str) -> RepositorySession:
        with self._lock:
            session = self._sessions.get(repository_id, RepositorySession(repository_id=repository_id, session_id=f"vc-{repository_id}", state="closed"))
            self._sessions[repository_id] = RepositorySession(repository_id=repository_id, session_id=session.session_id, state="closed")
            return self._sessions[repository_id]

    def get_metadata(self, repository_id: str) -> VersionControlMetadata | None:
        return self._metadata.get(repository_id)


class GitManager:
    """Git backend for repository operations using the local git CLI."""

    def _run_git(self, repository_path: str, args: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

    def _result(self, completed: subprocess.CompletedProcess[str], repository_path: str, command: list[str], metadata: dict[str, Any] | None = None) -> GitOperationResult:
        return GitOperationResult(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            repository_path=repository_path,
            command=tuple(command),
            metadata=metadata or {},
        )

    def init_repository(self, repository_path: str, bare: bool = False, repository_id: str | None = None) -> GitOperationResult:
        Path(repository_path).mkdir(parents=True, exist_ok=True)
        args = ["init", "--bare"] if bare else ["init", "--initial-branch=main"]
        completed = self._run_git(repository_path, args)
        if not bare and completed.returncode == 0:
            self._run_git(repository_path, ["config", "user.name", "Tangku Bot"])
            self._run_git(repository_path, ["config", "user.email", "tangku@example.com"])
        return self._result(completed, repository_path, args, metadata={"repository_id": repository_id, "bare": bare})

    def clone_repository(self, remote_url: str, target_path: str, timeout: float | None = None, repository_id: str | None = None) -> GitOperationResult:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        completed = self._run_git(str(target.parent), ["clone", remote_url, str(target.name)], timeout=timeout)
        return self._result(completed, str(target), ["clone", remote_url, str(target.name)], metadata={"repository_id": repository_id})

    def add(self, repository_path: str, paths: list[str] | None = None, repository_id: str | None = None) -> GitOperationResult:
        args = ["add", "--"] + (paths or ["."])
        completed = self._run_git(repository_path, args)
        return self._result(completed, repository_path, args, metadata={"repository_id": repository_id})

    def commit(self, repository_path: str, message: str, author: str | None = None, repository_id: str | None = None) -> Commit:
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])
        self._run_git(repository_path, ["config", "user.name", "Tangku Bot"])
        self._run_git(repository_path, ["config", "user.email", "tangku@example.com"])
        completed = self._run_git(repository_path, args)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout or "git commit failed")
        return Commit(
            commit_id=f"{repository_id or Path(repository_path).name}:{message}",
            repository_id=repository_id or Path(repository_path).name,
            message=message,
            author=author or "",
            timestamp="",
            metadata={"repository_path": repository_path, "exit_code": completed.returncode},
        )

    def status(self, repository_path: str, short: bool = False, repository_id: str | None = None) -> GitStatus:
        args = ["status", "--short"] if short else ["status"]
        completed = self._run_git(repository_path, args)
        branch = ""
        is_dirty = False
        for line in completed.stdout.splitlines():
            if line.startswith("On branch "):
                branch = line.replace("On branch ", "", 1).strip()
            if line.startswith("Changes") or line.startswith("Untracked") or line.startswith("modified"):
                is_dirty = True
        if not branch and completed.stdout:
            branch = "main"
        return GitStatus(
            repository_path=repository_path,
            branch=branch or "main",
            is_dirty=is_dirty,
            stdout=completed.stdout,
            stderr=completed.stderr,
            metadata={"repository_id": repository_id, "short": short},
        )

    def diff(self, repository_path: str, repository_id: str | None = None) -> GitDiff:
        completed = self._run_git(repository_path, ["diff"])
        return GitDiff(repository_path=repository_path, patch=completed.stdout, stdout=completed.stdout, stderr=completed.stderr, metadata={"repository_id": repository_id})

    def log(self, repository_path: str, repository_id: str | None = None, max_count: int | None = None) -> list[Commit]:
        args = ["log", "--format=%H%x00%s"]
        if max_count:
            args.extend(["-n", str(max_count)])
        completed = self._run_git(repository_path, args)
        commits: list[Commit] = []
        for entry in completed.stdout.splitlines():
            if not entry.strip():
                continue
            commit_id, message = entry.split("\x00", 1)
            commits.append(Commit(commit_id=commit_id[:12], repository_id=repository_id or Path(repository_path).name, message=message, metadata={"repository_path": repository_path}))
        return commits

    def create_branch(self, repository_path: str, branch_name: str, checkout: bool = False, repository_id: str | None = None) -> Branch:
        args = ["branch", branch_name]
        if checkout:
            args = ["checkout", "-b", branch_name]
        completed = self._run_git(repository_path, args)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr or completed.stdout or "git branch failed")
        return Branch(name=branch_name, repository_id=repository_id or Path(repository_path).name, metadata={"checkout": checkout, "repository_path": repository_path})

    def checkout(self, repository_path: str, branch_name: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["checkout", branch_name])
        return self._result(completed, repository_path, ["checkout", branch_name], metadata={"repository_id": repository_id})

    def list_branches(self, repository_path: str, all: bool = False, repository_id: str | None = None) -> list[str]:
        args = ["branch"] + (["--all"] if all else [])
        completed = self._run_git(repository_path, args)
        branches = [line.strip().lstrip("*").strip() for line in completed.stdout.splitlines() if line.strip()]
        return branches

    def create_tag(self, repository_path: str, tag_name: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["tag", tag_name])
        return self._result(completed, repository_path, ["tag", tag_name], metadata={"repository_id": repository_id})

    def push(self, repository_path: str, remote: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["push", remote, "HEAD:main"])
        return self._result(completed, repository_path, ["push", remote, "HEAD:main"], metadata={"repository_id": repository_id, "remote": remote})

    def pull(self, repository_path: str, remote: str | None = None, repository_id: str | None = None) -> GitOperationResult:
        args = ["pull"]
        if remote:
            args.append(remote)
        completed = self._run_git(repository_path, args)
        return self._result(completed, repository_path, args, metadata={"repository_id": repository_id})

    def fetch(self, repository_path: str, remote: str | None = None, repository_id: str | None = None) -> GitOperationResult:
        args = ["fetch"]
        if remote:
            args.append(remote)
        completed = self._run_git(repository_path, args)
        return self._result(completed, repository_path, args, metadata={"repository_id": repository_id})

    def merge(self, repository_path: str, branch_name: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["merge", branch_name])
        return self._result(completed, repository_path, ["merge", branch_name], metadata={"repository_id": repository_id})

    def rebase(self, repository_path: str, branch_name: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["rebase", branch_name])
        return self._result(completed, repository_path, ["rebase", branch_name], metadata={"repository_id": repository_id})

    def stash(self, repository_path: str, repository_id: str | None = None) -> GitOperationResult:
        completed = self._run_git(repository_path, ["stash", "push", "-u", "-m", "tangku-stash"])
        return self._result(completed, repository_path, ["stash", "push", "-u", "-m", "tangku-stash"], metadata={"repository_id": repository_id})

    def get_metadata(self, repository_path: str, repository_id: str | None = None) -> GitMetadata:
        return GitMetadata(
            name=repository_id or Path(repository_path).name,
            repository_type=RepositoryType.GIT,
            default_branch="main",
            repository_path=repository_path,
            metadata={"repository_id": repository_id},
        )

    def get_health(self, repository_path: str, repository_id: str | None = None) -> GitHealth:
        completed = self._run_git(repository_path, ["status", "--short"])
        status = "healthy" if completed.returncode == 0 else "degraded"
        return GitHealth(repository_path=repository_path, status=status, details={"repository_id": repository_id, "exit_code": completed.returncode})


class BranchManager(BranchManagerInterface):
    """Branch abstraction runtime."""

    def __init__(self) -> None:
        self._branches: Dict[str, Branch] = {}
        self._metadata: Dict[str, BranchMetadata] = {}
        self._lifecycles: Dict[str, BranchLifecycle] = {}
        self._lock = RLock()

    def create_branch(self, repository_id: str, branch_name: str, metadata: dict[str, Any] | None = None) -> Branch:
        branch = Branch(name=branch_name, repository_id=repository_id, metadata=metadata or {})
        with self._lock:
            self._branches[f"{repository_id}:{branch_name}"] = branch
            self._metadata[f"{repository_id}:{branch_name}"] = BranchMetadata(repository_id=repository_id, name=branch_name, metadata=metadata or {})
            self._lifecycles[f"{repository_id}:{branch_name}"] = BranchLifecycle(repository_id=repository_id, name=branch_name, state="created")
        return branch

    def switch_branch(self, repository_id: str, branch_name: str) -> Branch:
        branch = self.get_branch(repository_id, branch_name)
        with self._lock:
            self._lifecycles[f"{repository_id}:{branch_name}"] = BranchLifecycle(repository_id=repository_id, name=branch_name, state="active")
        return branch

    def get_branch(self, repository_id: str, branch_name: str) -> Branch:
        key = f"{repository_id}:{branch_name}"
        branch = self._branches.get(key)
        if branch is None:
            raise KeyError(branch_name)
        return branch

    def compare_branches(self, repository_id: str, source_branch: str, target_branch: str) -> dict[str, Any]:
        return {"repository_id": repository_id, "source_branch": source_branch, "target_branch": target_branch}

    def list_branches(self, repository_id: str) -> list[Branch]:
        return [branch for branch in self._branches.values() if branch.repository_id == repository_id]


class CommitManager(CommitManagerInterface):
    """Commit abstraction runtime."""

    def __init__(self) -> None:
        self._commits: Dict[str, Commit] = {}
        self._metadata: Dict[str, CommitMetadata] = {}
        self._history: Dict[str, list[Commit]] = {}
        self._graph: Dict[str, CommitGraph] = {}
        self._lock = RLock()

    def create_commit(self, repository_id: str, message: str, *, author: str = "", metadata: dict[str, Any] | None = None) -> Commit:
        commit = Commit(commit_id=f"{repository_id}:{len(self._commits)+1}", repository_id=repository_id, message=message, author=author, metadata=metadata or {})
        with self._lock:
            self._commits[commit.commit_id] = commit
            self._metadata[commit.commit_id] = CommitMetadata(repository_id=repository_id, commit_id=commit.commit_id, metadata=metadata or {})
            self._history.setdefault(repository_id, []).append(commit)
            self._graph[repository_id] = CommitGraph(repository_id=repository_id, nodes=[{"id": commit.commit_id, "message": message}], edges=[])
        return commit

    def get_commit(self, repository_id: str, commit_id: str) -> Commit:
        commit = self._commits.get(commit_id)
        if commit is None:
            raise KeyError(commit_id)
        return commit

    def list_commits(self, repository_id: str) -> list[Commit]:
        return list(self._history.get(repository_id, []))

    def get_history(self, repository_id: str) -> CommitHistory:
        return CommitHistory(repository_id=repository_id, commits=self.list_commits(repository_id))


class ChangeManager:
    """Change tracking runtime."""

    def __init__(self) -> None:
        self._changes: Dict[str, ChangeMetadata] = {}
        self._history: Dict[str, ChangeHistory] = {}
        self._lock = RLock()

    def track_change(self, repository_id: str, object_id: str, *, kind: str = "file", metadata: dict[str, Any] | None = None) -> ChangeMetadata:
        change = ChangeMetadata(repository_id=repository_id, change_id=f"{repository_id}:{object_id}", kind=kind, metadata=metadata or {})
        with self._lock:
            self._changes[change.change_id] = change
            self._history[repository_id] = ChangeHistory(repository_id=repository_id, entries=[{"change_id": change.change_id, "object_id": object_id, "kind": kind, **(metadata or {})}])
        return change

    def list_changes(self, repository_id: str) -> ChangeHistory:
        return self._history.get(repository_id, ChangeHistory(repository_id=repository_id))


class MergeManager(MergeManagerInterface):
    """Merge planning runtime without merge algorithms."""

    def __init__(self) -> None:
        self._merges: Dict[str, MergeMetadata] = {}
        self._contexts: Dict[str, MergeContext] = {}
        self._conflicts: Dict[str, ConflictMetadata] = {}
        self._lock = RLock()

    def plan_merge(self, repository_id: str, source_branch: str, target_branch: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        merge_metadata = MergeMetadata(repository_id=repository_id, source_branch=source_branch, target_branch=target_branch, metadata=metadata or {})
        with self._lock:
            self._merges[f"{repository_id}:{source_branch}->{target_branch}"] = merge_metadata
            self._contexts[repository_id] = MergeContext(repository_id=repository_id, state="planned", metadata=metadata or {})
        return {"repository_id": repository_id, "source_branch": source_branch, "target_branch": target_branch, "state": "planned"}

    def detect_conflicts(self, repository_id: str) -> list[ConflictMetadata]:
        return list(self._conflicts.values())


class DiffManager:
    """Structured diff runtime."""

    def __init__(self) -> None:
        self._diffs: Dict[str, DiffMetadata] = {}
        self._contexts: Dict[str, DiffContext] = {}
        self._lock = RLock()

    def create_diff(self, repository_id: str, object_id: str, metadata: dict[str, Any] | None = None) -> DiffMetadata:
        diff = DiffMetadata(repository_id=repository_id, object_id=object_id, metadata=metadata or {})
        with self._lock:
            self._diffs[f"{repository_id}:{object_id}"] = diff
            self._contexts[repository_id] = DiffContext(repository_id=repository_id, state="ready", metadata=metadata or {})
        return diff


class CollaborationManager:
    """Collaboration and review workflow runtime."""

    def __init__(self) -> None:
        self._reviews: Dict[str, ReviewMetadata] = {}
        self._sessions: Dict[str, ReviewSession] = {}
        self._permissions: Dict[str, RepositoryPermissions] = {}
        self._lock = RLock()

    def start_review(self, repository_id: str, branch: str, metadata: dict[str, Any] | None = None) -> ReviewSession:
        review_id = f"review-{repository_id}-{branch}"
        with self._lock:
            self._reviews[review_id] = ReviewMetadata(repository_id=repository_id, review_id=review_id, branch=branch, metadata=metadata or {})
            session = ReviewSession(repository_id=repository_id, review_id=review_id, state="active", metadata=metadata or {})
            self._sessions[review_id] = session
            return session

    def set_permissions(self, repository_id: str, roles: dict[str, str]) -> RepositoryPermissions:
        permissions = RepositoryPermissions(repository_id=repository_id, roles=roles)
        with self._lock:
            self._permissions[repository_id] = permissions
        return permissions
