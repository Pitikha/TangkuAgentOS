from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class PromptMetadata:
    prompt_id: str
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptVariables:
    variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.variables


@dataclass(frozen=True)
class PromptVersion:
    version: str
    changelog: str = ""


@dataclass(frozen=True)
class PromptTemplate:
    prompt_id: str
    content: str
    metadata: PromptMetadata
    version: PromptVersion
