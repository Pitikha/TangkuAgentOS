from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptVariable:
    name: str
    value: str = ''


@dataclass
class PromptContext:
    variables: dict[str, str] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    template_id: str
    content: str = ''
    variables: list[PromptVariable] = field(default_factory=list)


class PromptManager:
    """Manage prompt templates and prompt composition state."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register_template(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> PromptTemplate | None:
        return self._templates.get(template_id)


class PromptRegistry:
    """Registry for prompt templates."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> PromptTemplate | None:
        return self._templates.get(template_id)


class PromptBuilder:
    """Compose templates with simple variable substitution."""

    def build(self, template: PromptTemplate, context: PromptContext | None = None) -> str:
        ctx = context or PromptContext()
        content = template.content
        for variable in template.variables:
            content = content.replace(f"{{{{{variable.name}}}}}", ctx.variables.get(variable.name, variable.value))
        return content


class PromptTemplateManager:
    """Manage prompt template metadata."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def add(self, template: PromptTemplate) -> None:
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> PromptTemplate | None:
        return self._templates.get(template_id)


class PromptVersionManager:
    """Track prompt versions without implementing prompt engineering."""

    def __init__(self) -> None:
        self._versions: dict[str, dict[str, PromptTemplate]] = {}

    def add_version(self, template_id: str, version: str, template: PromptTemplate) -> None:
        self._versions.setdefault(template_id, {})[version] = template

    def get_version(self, template_id: str, version: str) -> PromptTemplate | None:
        return self._versions.get(template_id, {}).get(version)
