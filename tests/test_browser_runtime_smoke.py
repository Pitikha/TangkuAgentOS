from __future__ import annotations

from tangku_agentos.browser_runtime import (
    AutomationContext,
    BrowserAutomationManager,
    BrowserManager,
    BrowserSessionManager,
    ElementManager,
    PageManager,
    WebIntelligenceManager,
)


def test_browser_runtime_smoke() -> None:
    browser_manager = BrowserManager()
    session = browser_manager.create_session("browser-1", profile_id="default")
    assert session.session_id == "browser-1"

    browser_session_manager = BrowserSessionManager(browser_manager)
    reopened = browser_session_manager.open("browser-2", profile_id="research")
    assert reopened.session_id == "browser-2"

    page_manager = PageManager()
    page = page_manager.create_page("page-1", url="https://example.com")
    assert page.page_id == "page-1"

    element_manager = ElementManager()
    element = element_manager.register_element("button-1", element_type="button", selector="#submit")
    assert element.element_id == "button-1"

    automation_manager = BrowserAutomationManager()
    automation = automation_manager.create_sequence(
        "seq-1",
        actions=[{"action": "navigate", "target": "https://example.com"}, {"action": "click", "target": "button-1"}],
    )
    assert automation.sequence_id == "seq-1"

    intelligence_manager = WebIntelligenceManager()
    document = intelligence_manager.create_document("doc-1", title="Example", url="https://example.com")
    assert document.document_id == "doc-1"

    context = AutomationContext(sequence_id="seq-1", metadata={"mode": "safe"})
    assert context.sequence_id == "seq-1"
