from __future__ import annotations

from tangku_agentos.interface_layer.web_dashboard import ProductionWebDashboard
from tangku_agentos.interface_layer.web_dashboard_server import DashboardHTTPApp


def test_web_dashboard_renders_provider_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("providers", {"request_id": "req-1", "session_id": "session-1"})

    assert response.status == "ok"
    assert response.output["route"] == "providers"


def test_web_dashboard_renders_shell_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("shell", {"request_id": "req-2", "session_id": "session-2"})

    assert response.status == "ok"
    assert response.output["route"] == "shell"
    assert "features" in response.output


def test_dashboard_http_app_serves_shell_and_json_routes() -> None:
    app = DashboardHTTPApp()

    html_status, html_body, html_content = app.handle_request("/", {})
    assert html_status == 200
    assert b"Tangku AgentOS Dashboard" in html_content

    json_status, json_body, json_content = app.handle_request("/api/providers", {})
    assert json_status == 200
    assert json_body["route"] == "providers"
    assert "providers" in json_body


def test_web_dashboard_renders_workflows_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("workflows", {"request_id": "req-4", "session_id": "session-4"})

    assert response.status == "ok"
    assert response.output["route"] == "workflows"
    assert "workflows" in response.output
    assert "instances" in response.output
    assert isinstance(response.output["instances"], list)


def test_web_dashboard_renders_automation_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("automation", {"request_id": "req-5", "session_id": "session-5"})

    assert response.status == "ok"
    assert response.output["route"] == "automation"
    assert "jobs" in response.output
    assert "schedules" in response.output
    assert isinstance(response.output["jobs"], list)
    assert isinstance(response.output["schedules"], list)


def test_web_dashboard_renders_plugins_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("plugins", {"request_id": "req-6", "session_id": "session-6"})

    assert response.status == "ok"
    assert response.output["route"] == "plugins"
    assert "plugins" in response.output
    assert isinstance(response.output["plugins"], list)


def test_web_dashboard_renders_memory_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("memory", {"request_id": "req-7", "session_id": "session-7"})

    assert response.status == "ok"
    assert response.output["route"] == "memory"
    assert "records" in response.output
    assert isinstance(response.output["records"], list)


def test_web_dashboard_exposes_production_ui_capabilities() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("shell", {"request_id": "req-3", "session_id": "session-3"})

    assert response.status == "ok"
    assert response.output["layout"]["command_palette"] is True
    assert response.output["layout"]["split_layout"] is True
    assert response.output["desktop"]["ready"] is True
    assert response.output["accessibility"]["reduced_motion"] is True


def test_web_dashboard_renders_chat_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("chat", {"request_id": "req-8", "session_id": "session-8"})

    assert response.status == "ok"
    assert response.output["route"] == "chat"
    assert "providers" in response.output
    assert "models" in response.output
    assert "sections" in response.output


def test_web_dashboard_renders_system_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("system", {"request_id": "req-9", "session_id": "session-9"})

    assert response.status == "ok"
    assert response.output["route"] == "system"
    assert "environment" in response.output
    assert isinstance(response.output["environment"], dict)


def test_web_dashboard_renders_agents_route() -> None:
    dashboard = ProductionWebDashboard()
    response = dashboard.render_route("agents", {"request_id": "req-10", "session_id": "session-10"})

    assert response.status == "ok"
    assert response.output["route"] == "agents"
    assert "agents" in response.output
    assert isinstance(response.output["agents"], list)
    assert response.output["agent_count"] == len(response.output["agents"])


def test_dashboard_http_app_renders_rich_frontend_shell() -> None:
    app = DashboardHTTPApp()

    html_status, html_body, html_content = app.handle_request("/", {})
    assert html_status == 200
    assert b"Command Palette" in html_content
    assert b"Keyboard shortcuts" in html_content
    assert b"Desktop-ready" in html_content
