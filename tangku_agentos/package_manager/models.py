from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class PackageType(Enum):
    AGENT = 'agent'
    PLUGIN = 'plugin'
    TOOL = 'tool'
    WORKFLOW = 'workflow'
    TEMPLATE = 'template'
    KNOWLEDGE_PACK = 'knowledge_pack'
    SKILL_PACK = 'skill_pack'
    CAPABILITY_PACK = 'capability_pack'


@dataclass(frozen=True)
class PackageDependency:
    package_id: str
    version: str
    optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PackageVersion:
    version: str
    release_notes: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PackageMetadata:
    package_id: str
    name: str
    package_type: PackageType
    version: str = '0.0.1'
    description: str = ''
    dependencies: List[PackageDependency] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PackageManifest:
    package_id: str
    metadata: PackageMetadata
    files: List[str] = field(default_factory=list)
    entrypoint: str = ''
    dependencies: List[PackageDependency] = field(default_factory=list)
