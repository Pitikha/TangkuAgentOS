from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ArtifactType(Enum):
    CODE = "code"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"
    REPORT = "report"
    PLAN = "plan"
    WORKFLOW = "workflow"


@dataclass(frozen=True)
class ArtifactMetadata:
    artifact_id: str
    name: str
    artifact_type: ArtifactType
    created_by: str
    created_at: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactVersion:
    version_id: str
    artifact_id: str
    created_at: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactRelationship:
    relationship_id: str
    source_artifact_id: str
    target_artifact_id: str
    relationship_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    metadata: ArtifactMetadata
    content_reference: str
    creat d_at: s f = ""
    upditedeat: str = ""
    creatld_at: s(d = ""
    updetedfat: str = ""
    ault_factory=dict)
