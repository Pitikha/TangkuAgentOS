from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple


class PageState(Enum):
    LOADING = "loading"
    READY = "ready"
    STALE = "stale"
    CLOSED = "closed"


class ElementType(Enum):
    BUTTON = "button"
    FORM = "form"
    INPUT = "input"
    LINK = "link"
    TABLE = "table"
    IMAGE = "image"
    DOCUMENT = "document"
    FRAME = "frame"
    DIALOG = "dialog"
    GENERIC = "generic"


class ResourceType(Enum):
    DOCUMENT = "document"
    SCRIPT = "script"
    STYLESHEET = "stylesheet"
    IMAGE = "image"
    FONT = "font"
    MEDIA = "media"
    OTHER = "other"


@dataclass(frozen=True)
class BrowserSession:
    session_id: str
    profile_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserConfiguration:
    session_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserContext:
    session_id: str
    user_agent: str | None = None
    viewport: Tuple[int, int] | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserLifecycle:
    session_id: str
    state: str = "created"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserMetadata:
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserProfile:
    profile_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserStatistics:
    session_id: str
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrowserHealth:
    session_id: str
    status: str = "healthy"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageSession:
    page_id: str
    session_id: str
    url: str | None = None
    state: PageState = PageState.LOADING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageContext:
    page_id: str
    session_id: str
    state: PageState = PageState.LOADING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageMetadata:
    page_id: str
    url: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageHistory:
    page_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ElementContext:
    element_id: str
    element_type: ElementType = ElementType.GENERIC
    selector: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ElementMetadata:
    element_id: str
    element_type: ElementType = ElementType.GENERIC
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationSession:
    sequence_id: str
    session_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationContext:
    sequence_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationHistory:
    sequence_id: str
    entries: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AutomationRequest:
    request_id: str
    action: str
    target: str | None = None
    value: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutomationSequence:
    sequence_id: str
    actions: Tuple[Dict[str, Any], ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContentMetadata:
    document_id: str
    title: str | None = None
    url: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WebDocument:
    document_id: str
    title: str | None = None
    url: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceRelationship:
    source: str
    target: str
    relation: str = "references"


@dataclass(frozen=True)
class ResourceGraph:
    graph_id: str
    resources: Tuple[Dict[str, Any], ...] = ()
    relationships: Tuple[ResourceRelationship, ...] = ()
