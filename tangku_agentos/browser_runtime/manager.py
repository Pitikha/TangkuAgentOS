from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List, Tuple

from .models import (
    AutomationContext,
    AutomationHistory,
    AutomationRequest,
    AutomationSequence,
    AutomationSession,
    BrowserConfiguration,
    BrowserContext,
    BrowserHealth,
    BrowserLifecycle,
    BrowserMetadata,
    BrowserProfile,
    BrowserSession,
    BrowserStatistics,
    ContentMetadata,
    ElementContext,
    ElementMetadata,
    ElementType,
    PageContext,
    PageHistory,
    PageMetadata,
    PageSession,
    PageState,
    ResourceGraph,
    ResourceRelationship,
    WebDocument,
)


class BrowserManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, BrowserSession] = {}
        self._contexts: Dict[str, BrowserContext] = {}
        self._configurations: Dict[str, BrowserConfiguration] = {}
        self._metadata: Dict[str, BrowserMetadata] = {}
        self._statistics: Dict[str, BrowserStatistics] = {}
        self._health: Dict[str, BrowserHealth] = {}
        self._lifecycles: Dict[str, BrowserLifecycle] = {}
        self._profiles: Dict[str, BrowserProfile] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()

    def create_session(self, session_id: str, profile_id: str | None = None, metadata: dict[str, Any] | None = None) -> BrowserSession:
        with self._lock:
            session = BrowserSession(session_id=session_id, profile_id=profile_id, metadata=metadata or {})
            self._sessions[session_id] = session
            self._contexts[session_id] = BrowserContext(session_id=session_id, metadata=metadata or {})
            self._configurations[session_id] = BrowserConfiguration(session_id=session_id)
            self._metadata[session_id] = BrowserMetadata(session_id=session_id, metadata=metadata or {})
            self._statistics[session_id] = BrowserStatistics(session_id=session_id, stats={"pages": 0})
            self._health[session_id] = BrowserHealth(session_id=session_id)
            self._lifecycles[session_id] = BrowserLifecycle(session_id=session_id, state="created")
            self._history[session_id] = []
            return session

    def get_session(self, session_id: str) -> BrowserSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def set_profile(self, profile_id: str, profile: BrowserProfile) -> None:
        with self._lock:
            self._profiles[profile_id] = profile

    def get_profile(self, profile_id: str) -> BrowserProfile | None:
        with self._lock:
            return self._profiles.get(profile_id)

    def list_sessions(self) -> list[BrowserSession]:
        with self._lock:
            return list(self._sessions.values())


class BrowserRegistry:
    def __init__(self) -> None:
        self._sessions: Dict[str, BrowserSession] = {}
        self._lock = RLock()

    def register(self, session: BrowserSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def resolve(self, session_id: str) -> BrowserSession | None:
        with self._lock:
            return self._sessions.get(session_id)


class BrowserSessionManager:
    def __init__(self, browser_manager: BrowserManager | None = None) -> None:
        self._browser_manager = browser_manager or BrowserManager()
        self._lock = RLock()

    def open(self, session_id: str, profile_id: str | None = None, metadata: dict[str, Any] | None = None) -> BrowserSession:
        with self._lock:
            return self._browser_manager.create_session(session_id, profile_id=profile_id, metadata=metadata)

    def close(self, session_id: str) -> None:
        with self._lock:
            self._browser_manager._lifecycles[session_id] = BrowserLifecycle(session_id=session_id, state="closed")


class BrowserContextManager:
    def __init__(self) -> None:
        self._contexts: Dict[str, BrowserContext] = {}
        self._lock = RLock()

    def update(self, session_id: str, user_agent: str | None = None, viewport: tuple[int, int] | None = None) -> BrowserContext:
        with self._lock:
            context = BrowserContext(session_id=session_id, user_agent=user_agent, viewport=viewport, metadata={})
            self._contexts[session_id] = context
            return context


class BrowserLifecycleManager:
    def __init__(self) -> None:
        self._lifecycles: Dict[str, BrowserLifecycle] = {}
        self._lock = RLock()

    def transition(self, session_id: str, state: str) -> BrowserLifecycle:
        with self._lock:
            lifecycle = BrowserLifecycle(session_id=session_id, state=state)
            self._lifecycles[session_id] = lifecycle
            return lifecycle


class BrowserConfigurationManager:
    def __init__(self) -> None:
        self._configurations: Dict[str, BrowserConfiguration] = {}
        self._lock = RLock()

    def set(self, session_id: str, settings: dict[str, Any]) -> BrowserConfiguration:
        with self._lock:
            configuration = BrowserConfiguration(session_id=session_id, settings=settings)
            self._configurations[session_id] = configuration
            return configuration


class BrowserMetadataManager:
    def __init__(self) -> None:
        self._metadata: Dict[str, BrowserMetadata] = {}
        self._lock = RLock()

    def set(self, session_id: str, metadata: dict[str, Any]) -> BrowserMetadata:
        with self._lock:
            browser_metadata = BrowserMetadata(session_id=session_id, metadata=metadata)
            self._metadata[session_id] = browser_metadata
            return browser_metadata


class BrowserStatisticsManager:
    def __init__(self) -> None:
        self._stats: Dict[str, BrowserStatistics] = {}
        self._lock = RLock()

    def record(self, session_id: str, key: str, value: Any) -> BrowserStatistics:
        with self._lock:
            stats = self._stats.get(session_id, BrowserStatistics(session_id=session_id, stats={}))
            new_stats = dict(stats.stats)
            new_stats[key] = value
            browser_stats = BrowserStatistics(session_id=session_id, stats=new_stats)
            self._stats[session_id] = browser_stats
            return browser_stats


class BrowserHealthManager:
    def __init__(self) -> None:
        self._health: Dict[str, BrowserHealth] = {}
        self._lock = RLock()

    def set(self, session_id: str, status: str, details: dict[str, Any] | None = None) -> BrowserHealth:
        with self._lock:
            health = BrowserHealth(session_id=session_id, status=status, details=details or {})
            self._health[session_id] = health
            return health


class PageManager:
    def __init__(self) -> None:
        self._pages: Dict[str, PageSession] = {}
        self._contexts: Dict[str, PageContext] = {}
        self._metadata: Dict[str, PageMetadata] = {}
        self._history: Dict[str, PageHistory] = {}
        self._lock = RLock()

    def create_page(self, page_id: str, session_id: str | None = None, url: str | None = None, metadata: dict[str, Any] | None = None) -> PageSession:
        with self._lock:
            page = PageSession(page_id=page_id, session_id=session_id or "default", url=url, state=PageState.READY, metadata=metadata or {})
            self._pages[page_id] = page
            self._contexts[page_id] = PageContext(page_id=page_id, session_id=page.session_id, state=page.state, metadata=metadata or {})
            self._metadata[page_id] = PageMetadata(page_id=page_id, url=url, metadata=metadata or {})
            self._history[page_id] = PageHistory(page_id=page_id, entries=[{"url": url, "state": page.state.value}])
            return page


class PageRegistry:
    def __init__(self) -> None:
        self._pages: Dict[str, PageSession] = {}
        self._lock = RLock()

    def register(self, page: PageSession) -> None:
        with self._lock:
            self._pages[page.page_id] = page


class ElementManager:
    def __init__(self) -> None:
        self._elements: Dict[str, ElementContext] = {}
        self._metadata: Dict[str, ElementMetadata] = {}
        self._lock = RLock()

    def register_element(self, element_id: str, element_type: str | ElementType = ElementType.GENERIC, selector: str | None = None, metadata: dict[str, Any] | None = None) -> ElementContext:
        with self._lock:
            resolved_type = element_type if isinstance(element_type, ElementType) else ElementType(element_type)
            element = ElementContext(element_id=element_id, element_type=resolved_type, selector=selector, metadata=metadata or {})
            self._elements[element_id] = element
            self._metadata[element_id] = ElementMetadata(element_id=element_id, element_type=resolved_type, metadata=metadata or {})
            return element


class ElementRegistry:
    def __init__(self) -> None:
        self._elements: Dict[str, ElementContext] = {}
        self._lock = RLock()

    def register(self, element: ElementContext) -> None:
        with self._lock:
            self._elements[element.element_id] = element


class BrowserAutomationManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, AutomationSession] = {}
        self._contexts: Dict[str, AutomationContext] = {}
        self._history: Dict[str, AutomationHistory] = {}
        self._lock = RLock()

    def create_sequence(self, sequence_id: str, session_id: str | None = None, actions: list[dict[str, Any]] | None = None, metadata: dict[str, Any] | None = None) -> AutomationSequence:
        with self._lock:
            sequence = AutomationSequence(sequence_id=sequence_id, actions=tuple(actions or []), metadata=metadata or {})
            self._sessions[sequence_id] = AutomationSession(sequence_id=sequence_id, session_id=session_id, metadata=metadata or {})
            self._contexts[sequence_id] = AutomationContext(sequence_id=sequence_id, metadata=metadata or {})
            self._history[sequence_id] = AutomationHistory(sequence_id=sequence_id, entries=[])
            return sequence

    def queue_request(self, sequence_id: str, request: AutomationRequest) -> AutomationRequest:
        with self._lock:
            history = self._history.get(sequence_id, AutomationHistory(sequence_id=sequence_id))
            self._history[sequence_id] = AutomationHistory(sequence_id=sequence_id, entries=list(history.entries) + [{"request": request.action, "target": request.target}])
            return request


class AutomationRegistry:
    def __init__(self) -> None:
        self._sequences: Dict[str, AutomationSequence] = {}
        self._lock = RLock()

    def register(self, sequence: AutomationSequence) -> None:
        with self._lock:
            self._sequences[sequence.sequence_id] = sequence


class WebIntelligenceManager:
    def __init__(self) -> None:
        self._documents: Dict[str, WebDocument] = {}
        self._metadata: Dict[str, ContentMetadata] = {}
        self._graphs: Dict[str, ResourceGraph] = {}
        self._lock = RLock()

    def create_document(self, document_id: str, title: str | None = None, url: str | None = None, metadata: dict[str, Any] | None = None) -> WebDocument:
        with self._lock:
            document = WebDocument(document_id=document_id, title=title, url=url, metadata=metadata or {})
            self._documents[document_id] = document
            self._metadata[document_id] = ContentMetadata(document_id=document_id, title=title, url=url, metadata=metadata or {})
            self._graphs[document_id] = ResourceGraph(graph_id=document_id, resources=(), relationships=())
            return document

    def register_graph(self, graph_id: str, resources: list[dict[str, Any]] | None = None, relationships: list[dict[str, Any]] | None = None) -> ResourceGraph:
        with self._lock:
            graph = ResourceGraph(graph_id=graph_id, resources=tuple(resources or []), relationships=tuple([ResourceRelationship(**item) for item in (relationships or [])]))
            self._graphs[graph_id] = graph
            return graph
