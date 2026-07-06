from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RepositoryType(Enum):
    GIT = "git"
    MERCURIAL = "mercurial"
    SVN = "svn"
    FILESYSTEM = "filesystem"


@dataclass(frozen=True)
class RepositoryMetadata:
    name: str
    description: str = ""
    repository_type: RepositoryType = RepositoryType.GIT
    url: str = ""
    default_branch: str = "main"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Repository:
    repository_id: str
    metadata: RepositoryMetadata
    branches: List["Branch"] = field(default_factory=list)
    commits: List["Commit"] = field(default_factory=list)
    pull_requests: List["PullRequest"] = field(default_factory=list)
    issues: List["Issue"] = field(default_factory=list)
    releases: List["Release"] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: "Version" | None = None
    metadata_map: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Branch:
    name: str
    repository_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Commit:
    commit_id: str
    repository_id: str
    message: str
    author: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PullRequest:
    pr_id: str
    repository_id: str
    source_branch: str
    target_branch: str
    title: str
    description: str = ""
    status: str = "open"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Issue:
    issue_id: str
    repository_id: str
    title: str
    description: str = ""
    status: str = "open"
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Release:
    release_id: str
    repository_id: str
    version: str
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Version:
    repository_id: str
    tag: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryContext:
    repository_id: str
    state: str = "registered"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositorySession:
    repository_id: str
    session_id: str
    state: str = "open"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryLifecycle:
    repository_id: str
    state: str = "registered"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryConfiguration:
    repository_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryStatistics:
    repository_id: str
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryHealth:
    repository_id: str
    status: str = "healthy"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VersionControlMetadata:
    repository_id: str
    provider: str = "abstract"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChangeMetadata:
    repository_id: str
    change_id: str
    kind: str = "file"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChangeHistory:
    repository_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class BranchMetadata:
    repository_id: str
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BranchLifecycle:
    repository_id: str
    name: str
    state: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommitMetadata:
    repository_id: str
    commit_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommitHistory:
    repository_id: str
    commits: List[Commit] = field(default_factory=list)


@dataclass(frozen=True)
class CommitGraph:
    repository_id: str
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MergeMetadata:
    repository_id: str
    source_branch: str
    target_branch: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MergeContext:
    repository_id: str
    state: str = "planned"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConflictMetadata:
    repository_id: str
    conflict_id: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiffMetadata:
    repository_id: str
    object_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiffContext:
    repository_id: str
    state: str = "ready"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewMetadata:
    repository_id: str
    review_id: str
    branch: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewSession:
    repository_id: str
    review_id: str
    state: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryPermissions:
    repository_id: str
    roles: Dict[str, str] = field(default_factory=dict)
