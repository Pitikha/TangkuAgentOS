from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ProgrammingLanguage(Enum):
    PYTHON = "python"
    JAVA = "java"
    KOTLIN = "kotlin"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    SWIFT = "swift"
    PHP = "php"
    RUBY = "ruby"
    DART = "dart"
    LUA = "lua"
    BASH = "bash"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"


@dataclass(frozen=True)
class ProgrammingLanguageProfile:
    language: ProgrammingLanguage
    file_extensions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CodingConfigurationModel:
    session_id: str
    description: str = ""
    default_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodingStatisticsModel:
    session_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodingSession:
    session_id: str
    configuration: CodingConfigurationModel
    active: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CodingPlatformMetadata:
    name: str = "coding_platform"
    description: str = "Architectural foundation for Tangku coding platform"
    supported_languages: List[ProgrammingLanguage] = field(default_factory=list)


@dataclass
class CodingPlatformConfig:
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
