from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from .models import Branch, Commit, Issue, PullRequest, Release, Repository, Version


class RepositoryManagerInterface(ABC):
    """Interface for repository intelligence management."""

    @abstractmethod
    def scan_repository(self, repository_id: str) -> Repository:
        ...

    @abstractmethod
    def get_repository(self, repository_id: str) -> Repository:
        ...

    @abstractmethod
    def list_repositories(self) -> list[Repository]:
        ...


class RepositoryRegistryInterface(ABC):
    """Interface for repository registry."""

    @abstractmethod
    def register(self, repository: Repository) -> None:
        ...

    @abstractmethod
    def resolve(self, repository_id: str) -> Repository:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class RepositoryScanner(ABC):
    """Interface for scanning repositories."""

    @abstractmethod
    def scan(self, repository_id: str) -> Repository:
        ...


class BranchManager(ABC):
    @abstractmethod
    def list_branches(self, repository_id: str) -> list[Branch]:
        ...

    @abstractmethod
    def get_branch(self, repository_id: str, branch_name: str) -> Branch:
        ...


class CommitManager(ABC):
    @abstractmethod
    def list_commits(self, repository_id: str, branch_name: str | None = None) -> list[Commit]:
        ...

    @abstractmethod
    def get_commit(self, repository_id: str, commit_id: str) -> Commit:
        ...


class MergeManager(ABC):
    @abstractmethod
    def plan_merge(self, source_branch: str, target_branch: str, repository_id: str) -> dict[str, Any]:
        ...


class PullRequestManager(ABC):
    @abstractmethod
    def create_pull_request(self, repository_id: str, source_branch: str, target_branch: str, title: str) -> PullRequest:
        ...

    @abstractmethod
    def list_pull_requests(self, repository_id: str) -> list[PullRequest]:
        ...


class IssueManager(ABC):
    @abstractmethod
    def list_issues(self, repository_id: str) -> list[Issue]:
        ...

    @abstractmethod
    def get_issue(self, repository_id: str, issue_id: str) -> Issue:
        ...


class ReleaseManager(ABC):
    @abstractmethod
    def list_releases(self, repository_id: str) -> list[Release]:
        ...

    @abstractmethod
    def get_release(self, repository_id: str, release_id: str) -> Release:
        ...


class TagManager(ABC):
    @abstractmethod
    def list_tags(self, repository_id: str) -> list[str]:
        ...

    @abstractmethod
    def get_tag(self, repository_id: str, tag_name: str) -> str:
        ...


class VersionManager(ABC):
    @abstractmethod
    def get_version(self, repository_id: str) -> Version:
        ...

    @abstractmethod
    def set_version(self, repository_id: str, version: Version) -> None:
        ...
