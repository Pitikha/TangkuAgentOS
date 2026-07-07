from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import PromptMetadata, PromptTemplate, PromptVariables, PromptVersion


class PromptManager(ABC):
    """Interface for managing prompts."""

    @abstractmethod
    def register_prompt(self, prompt: PromptTemplate) -> None:
        ...

    @abstractmethod
    def get_prompt(self, prompt_id: str) -> PromptTemplate:
        ...

    @abstractmethod
    def list_prompts(self) -> list[PromptTemplate]:
        ...


class PromptRegistry(ABC):
    """Interface for prompt registry operations."""

    @abstractmethod
    def register(self, prompt: PromptTemplate) -> None:
        ...

    @abstractmethod
    def resolve(self, prompt_id: str) -> PromptTemplate:
        ...

    @abstractmethod
    def list(self) -> list[PromptTemplate]:
        ...


class PromptBuilder(ABC):
    """Interface for building prompts."""

    @abstractmethod
    def build(self, template: PromptTemplate, variables: PromptVariables) -> str:
        ...


class PromptTemplate(ABC):
    """Interface for prompt template definitions."""

    @abstractmethod
    def render(self, variables: PromptVariables) -> str:
        ...


class PromptVariables(ABC):
    """Interface for prompt variables."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


class PromptMetadata(ABC):
    """Interface for prompt metadata."""

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        ...


class PromptVersion(ABC):
    """Interface for prompt versioning."""

    @abstractmethod
    def get_version(self) -> str:
        ...
