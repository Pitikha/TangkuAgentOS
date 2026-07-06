from __future__ import annotations

from typing import Any

from ..automation_runtime.runtime import AutomationManager
from ..browser_runtime.manager import BrowserManager
from ..coordination.runtime import MultiAgentManager
from ..memory_engine import MemoryManager
from ..plugin_runtime.runtime import PluginManager
from ..provider_runtime.dashboard import ProviderDashboard
from ..provider_runtime.hub import ProviderHub
from ..workflow_engine.manager import WorkflowManager
from .interfaces import WebDashboardInterface
from .models import InterfaceEvent, InterfaceMetadata, InterfaceRequest, InterfaceResponse, InterfaceType


class ProductionWebDashboard(WebDashboardInterface):
    """Concrete web dashboard adapter that exposes the existing backend services via the interface layer."""

    def __init__(self, *, hub: ProviderHub | None = None, workflow_manager: WorkflowManager | None = None, automation_manager: AutomationManager | None = None, browser_manager: BrowserManager | None = None, multi_agent_manager: MultiAgentManager | None = None, plugin_manager: PluginManager | None = None, memory_manager: MemoryManager | None = None) -> None:
        self._hub = hub or ProviderHub()
        self._workflow_manager = workflow_manager or WorkflowManager()
        self._automation_manager = automation_manager or AutomationManager()
        self._browser_manager = browser_manager or BrowserManager()
        self._multi_agent_manager = multi_agent_manager or MultiAgentManager()
        self._plugin_manager = plugin_manager or PluginManager()
        self._memory_manager = memory_manager or MemoryManager()
        self._provider_dashboard = ProviderDashboard(self._hub)
        self._initialized = False

    def initialize(self, metadata: InterfaceMetadata) -> None:
        self._initialized = True

    def handle_request(self, request: InterfaceRequest) -> InterfaceResponse:
        route = request.command
        payload = request.payload or {}
        if route == "shell":
            return self._build_shell(payload)
        if route == "providers":
            return self._build_providers(payload)
        if route == "chat":
            return self._build_chat(payload)
        if route == "workflows":
            return self._build_workflows(payload)
        if route == "automation":
            return self._build_automation(payload)
        if route == "agents":
            return self._build_agents(payload)
        if route == "browser":
            return self._build_browser(payload)
        if route == "plugins":
            return self._build_plugins(payload)
        if route == "memory":
            return self._build_memory(payload)
        if route == "system":
            return self._build_system(payload)
        if route == "settings":
            return self._build_settings(payload)
        return self._build_shell(payload)

    def supports_streaming(self) -> bool:
        return True

    def shutdown(self) -> None:
        self._initialized = False

    def render_route(self, route: str, payload: dict[str, Any]) -> InterfaceResponse:
        request = InterfaceRequest(request_id="dashboard-route", session_id="default", interface_type=InterfaceType.WEB_DASHBOARD, command=route, payload=payload)
        return self.handle_request(request)

    def push_update(self, update: InterfaceEvent) -> None:
        return None

    def _build_shell(self, payload: dict[str, Any]) -> InterfaceResponse:
        return InterfaceResponse(
            request_id=payload.get("request_id", "shell"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "shell",
                "layout": {
                    "sidebar": True,
                    "topbar": True,
                    "statusbar": True,
                    "breadcrumbs": True,
                    "notifications": True,
                    "command_palette": True,
                    "search": True,
                    "workspace_switcher": True,
                    "theme_switcher": True,
                    "dockable_panels": True,
                    "split_layout": True,
                    "responsive": True,
                    "keyboard_shortcuts": True,
                    "mobile_support": True,
                    "loading_states": True,
                    "error_states": True,
                    "animations": True,
                },
                "desktop": {
                    "ready": True,
                    "window_management": True,
                    "file_dialogs": True,
                    "notifications": True,
                    "tray_icon": True,
                    "startup_options": True,
                },
                "accessibility": {
                    "keyboard_navigation": True,
                    "screen_reader_support": True,
                    "high_contrast": True,
                    "reduced_motion": True,
                    "scalable_fonts": True,
                    "focus_indicators": True,
                },
                "realtime": {
                    "enabled": True,
                    "transport": "sse",
                    "events": ["streaming", "provider_status", "workflow_execution", "automation_progress", "agent_activity", "browser_activity", "memory_updates", "system_metrics"],
                },
                "onboarding": {
                    "enabled": True,
                    "steps": ["welcome", "hardware_detection", "provider_detection", "api_keys", "recommended_models", "benchmark", "profile"],
                },
                "features": ["chat", "providers", "workflows", "automation", "agents", "browser", "plugins", "memory", "system", "settings"],
                "navigation": ["chat", "providers", "workflows", "automation", "agents", "browser", "plugins", "memory", "system", "settings"],
                "theme": payload.get("theme", "system"),
                "workspaces": ["default", "research", "ops", "dev"],
                "status": "production-ready",
            },
        )

    def _build_providers(self, payload: dict[str, Any]) -> InterfaceResponse:
        cards = self._provider_dashboard.build_cards()
        provider_details = self._hub.list_provider_details()
        return InterfaceResponse(
            request_id=payload.get("request_id", "providers"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "providers",
                "providers": cards,
                "provider_details": provider_details,
                "models": self._hub.list_models() if hasattr(self._hub, "list_models") else [],
                "default_provider": self._hub.resolve_default_provider(),
                "provider_count": len(provider_details),
                "actions": ["add", "remove", "edit", "test", "benchmark", "set_default", "view_logs"],
                "sections": ["overview", "providers", "models", "benchmarks", "diagnostics", "settings"],
            },
        )

    def _build_chat(self, payload: dict[str, Any]) -> InterfaceResponse:
        providers = [
            {
                "provider_id": provider["provider_id"],
                "display_name": provider["display_name"],
                "provider_type": provider["provider_type"],
                "status": provider.get("status", "registered"),
                "connected": bool(provider.get("connected", False)),
                "capabilities": provider.get("capabilities", {}),
            }
            for provider in self._hub.list_provider_details()
        ]
        models = self._hub.list_models() if hasattr(self._hub, "list_models") else []
        return InterfaceResponse(
            request_id=payload.get("request_id", "chat"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "chat",
                "default_provider": self._hub.resolve_default_provider(),
                "providers": providers,
                "models": models,
                "available_models": [model.get("model_id") for model in models],
                "conversations": [],
                "recent_conversations": [],
                "active_conversation_count": 0,
                "pinned": [],
                "folders": [],
                "provider_selector": True,
                "model_selector": True,
                "memory_indicator": True,
                "streaming": True,
                "markdown": True,
                "syntax_highlighting": True,
                "image_support": True,
                "audio_support": True,
                "drag_and_drop": True,
                "token_usage": True,
                "token_limit": 8192,
                "actions": ["new_chat", "rename", "delete", "export", "import", "duplicate", "share"],
                "sections": ["messages", "settings", "history", "search", "analytics"],
            },
        )

    def _build_workflows(self, payload: dict[str, Any]) -> InterfaceResponse:
        workflows = []
        workflow_instances = []
        if hasattr(self._workflow_manager, "list_workflows"):
            workflows = [
                {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name or workflow.workflow_id,
                    "description": workflow.description,
                    "node_count": len(workflow.nodes),
                    "edge_count": len(workflow.edges),
                    "status": "ready",
                    "created_by": workflow.metadata.created_by,
                    "tags": list(workflow.metadata.tags),
                }
                for workflow in self._workflow_manager.list_workflows()
            ]
        if hasattr(self._workflow_manager, "list_instances"):
            workflow_instances = [
                {
                    "instance_id": instance.instance_id,
                    "workflow_id": instance.workflow.workflow_id,
                    "state": instance.state.value if hasattr(instance.state, "value") else str(instance.state),
                    "created_at": instance.created_at,
                    "updated_at": instance.updated_at,
                }
                for instance in self._workflow_manager.list_instances()
            ]
        return InterfaceResponse(
            request_id=payload.get("request_id", "workflows"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "workflows",
                "workflows": workflows,
                "instances": workflow_instances,
                "status": "ready",
                "nodes": ["condition", "loop", "browser", "tool", "agent", "memory", "schedule"],
                "debug": True,
                "live_execution": True,
            },
        )

    def _build_automation(self, payload: dict[str, Any]) -> InterfaceResponse:
        jobs = []
        schedules = []
        if hasattr(self._automation_manager, "list_jobs"):
            jobs = [
                {
                    "job_id": getattr(job, "job_id", None),
                    "name": getattr(job, "name", ""),
                    "job_type": getattr(job, "job_type", ""),
                    "dependencies": getattr(job, "dependencies", []),
                    "metadata": getattr(job, "metadata", {}),
                }
                for job in self._automation_manager.list_jobs()
            ]
        if hasattr(self._automation_manager, "list_schedules"):
            schedules = [
                {
                    "schedule_id": schedule.schedule_id,
                    "schedule_type": schedule.schedule_type,
                    "config": schedule.config,
                    "metadata": schedule.metadata,
                }
                for schedule in self._automation_manager.list_schedules()
            ]
        return InterfaceResponse(
            request_id=payload.get("request_id", "automation"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "automation",
                "jobs": jobs,
                "schedules": schedules,
                "sections": ["scheduled", "running", "completed", "failed", "retry_queue", "logs", "metrics", "history"],
                "actions": ["pause", "resume", "cancel", "duplicate", "import", "export"],
            },
        )

    def _build_agents(self, payload: dict[str, Any]) -> InterfaceResponse:
        agents = []
        if hasattr(self._multi_agent_manager, "discover_agents"):
            discovered = self._multi_agent_manager.discover_agents()
            agents = [
                {
                    "agent_id": getattr(getattr(agent, "descriptor", None), "agent_id", getattr(agent, "agent_id", None)),
                    "name": getattr(agent, "name", None) or getattr(getattr(agent, "descriptor", None), "name", getattr(agent, "agent_id", "agent")),
                    "role": getattr(getattr(agent, "profile", None), "role", None) or "agent",
                    "description": getattr(getattr(agent, "profile", None), "description", ""),
                    "status": getattr(getattr(agent, "state", None), "value", str(getattr(agent, "state", "unknown"))),
                    "health": {
                        "status": getattr(getattr(agent, "health", None), "status", "unknown"),
                        "message": getattr(getattr(agent, "health", None), "message", ""),
                    },
                    "capabilities": [getattr(capability, "name", str(capability)) for capability in getattr(agent, "capabilities", [])],
                    "metadata": getattr(agent, "metadata", {}).to_dict() if hasattr(getattr(agent, "metadata", {}), "to_dict") else dict(getattr(agent, "metadata", {})),
                    "context": {
                        "agent_id": getattr(getattr(agent, "context", None), "agent_id", None),
                        "name": getattr(getattr(agent, "context", None), "name", None),
                        "agent_type": getattr(getattr(agent, "context", None), "agent_type", None),
                    },
                    "last_seen": getattr(agent, "last_seen", None),
                }
                for agent in discovered
            ]
        metrics = self._multi_agent_manager.get_runtime_metrics() if hasattr(self._multi_agent_manager, "get_runtime_metrics") else {}
        return InterfaceResponse(
            request_id=payload.get("request_id", "agents"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "agents",
                "agents": agents,
                "agent_count": len(agents),
                "actions": ["create", "pause", "resume", "remove", "debug"],
                "live_execution": True,
                "sections": ["overview", "activity", "logs", "settings"],
                "metrics": metrics,
            },
        )

    def _build_browser(self, payload: dict[str, Any]) -> InterfaceResponse:
        sessions = []
        if hasattr(self._browser_manager, "list_sessions"):
            sessions = [session.to_dict() if hasattr(session, "to_dict") else {"session_id": getattr(session, "session_id", None)} for session in self._browser_manager.list_sessions()]
        return InterfaceResponse(
            request_id=payload.get("request_id", "browser"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "browser",
                "sessions": sessions,
                "views": ["tabs", "profiles", "cookies", "downloads", "console", "dom", "storage", "network"],
                "automation_controls": True,
            },
        )

    def _build_plugins(self, payload: dict[str, Any]) -> InterfaceResponse:
        plugins = []
        if hasattr(self._plugin_manager, "list_plugins"):
            plugins = [
                {
                    "plugin_id": plugin.plugin_id,
                    "name": plugin.name,
                    "description": getattr(plugin, "description", ""),
                    "enabled": getattr(plugin, "enabled", False),
                    "version": getattr(plugin, "version", ""),
                    "author": getattr(plugin, "metadata", {}).get("author", ""),
                    "homepage": getattr(plugin, "metadata", {}).get("homepage", ""),
                    "capabilities": getattr(plugin, "capabilities", []),
                    "dependencies": getattr(plugin, "dependencies", []),
                    "metadata": getattr(plugin, "metadata", {}),
                    "status": self._plugin_manager.lifecycle_manager.get_state(plugin.plugin_id) if hasattr(self._plugin_manager, "lifecycle_manager") else "unknown",
                }
                for plugin in self._plugin_manager.list_plugins()
            ]
        return InterfaceResponse(
            request_id=payload.get("request_id", "plugins"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "plugins",
                "plugins": plugins,
                "actions": ["install", "update", "remove", "enable", "disable", "configure"],
                "sections": ["installed", "available", "updates", "permissions", "dependencies", "ratings"],
            },
        )

    def _build_memory(self, payload: dict[str, Any]) -> InterfaceResponse:
        records = []
        if hasattr(self._memory_manager, "list_records"):
            for record in self._memory_manager.list_records():
                entries = [
                    {
                        "entry_id": entry.entry_id,
                        "type": entry.type.value if hasattr(entry.type, "value") else str(entry.type),
                        "content_preview": entry.content if isinstance(entry.content, dict) else str(entry.content),
                        "metadata": {
                            "created_by": entry.metadata.created_by,
                            "tags": list(entry.metadata.tags),
                        },
                    }
                    for entry in record.entries
                ]
                records.append(
                    {
                        "record_id": record.record_id,
                        "namespace": record.namespace,
                        "entry_count": len(record.entries),
                        "metadata": {
                            "created_by": record.metadata.created_by,
                            "created_at": record.metadata.created_at,
                            "updated_at": record.metadata.updated_at,
                            "tags": list(record.metadata.tags),
                        },
                        "entries": entries,
                    }
                )
        return InterfaceResponse(
            request_id=payload.get("request_id", "memory"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "memory",
                "records": records,
                "record_count": len(records),
                "sections": ["short_term", "long_term", "semantic", "workflow", "agent"],
                "actions": ["search", "filter", "edit", "delete", "export", "import", "visualize"],
            },
        )

    def _build_system(self, payload: dict[str, Any]) -> InterfaceResponse:
        provider_list = self._hub.list_provider_details()
        memory_records = self._memory_manager.list_records() if hasattr(self._memory_manager, "list_records") else []
        browser_sessions = self._browser_manager.list_sessions() if hasattr(self._browser_manager, "list_sessions") else []
        agents = self._multi_agent_manager.discover_agents() if hasattr(self._multi_agent_manager, "discover_agents") else []
        metrics = self._multi_agent_manager.get_runtime_metrics() if hasattr(self._multi_agent_manager, "get_runtime_metrics") else {}
        return InterfaceResponse(
            request_id=payload.get("request_id", "system"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "system",
                "kernel": {"status": "healthy", "version": "1.0.0-beta"},
                "hardware": self._hub.detect_hardware() if hasattr(self._hub, "detect_hardware") else {},
                "environment": {
                    "providers": len(provider_list),
                    "browser_sessions": len(browser_sessions),
                    "memory_records": len(memory_records),
                    "workflow_count": len(self._workflow_manager.list_workflows()) if hasattr(self._workflow_manager, "list_workflows") else 0,
                    "plugin_count": len(self._plugin_manager.list_plugins()) if hasattr(self._plugin_manager, "list_plugins") else 0,
                    "agent_count": len(agents),
                },
                "providers": provider_list,
                "agents": [
                    {
                        "agent_id": getattr(getattr(agent, "descriptor", None), "agent_id", getattr(agent, "agent_id", None)),
                        "name": getattr(agent, "name", None) or getattr(getattr(agent, "descriptor", None), "agent_id", "agent"),
                        "status": getattr(agent, "status", "ready"),
                    }
                    for agent in agents
                ],
                "plugins": [plugin.plugin_id for plugin in self._plugin_manager.list_plugins()] if hasattr(self._plugin_manager, "list_plugins") else [],
                "browser_sessions": [session.session_id for session in browser_sessions],
                "event_rate": 0,
                "diagnostics": ["cpu", "ram", "gpu", "storage", "runtime"],
                "metrics": metrics,
            },
        )

    def _build_settings(self, payload: dict[str, Any]) -> InterfaceResponse:
        return InterfaceResponse(
            request_id=payload.get("request_id", "settings"),
            session_id=payload.get("session_id", "default"),
            status="ok",
            output={
                "route": "settings",
                "sections": ["Providers", "Models", "Appearance", "Themes", "Memory", "Browser", "Plugins", "Automation", "Workflow", "Security", "API Keys", "Notifications", "Updates", "Experimental"],
                "theme": {
                    "current": payload.get("theme", "system"),
                    "available": ["system", "light", "dark"],
                    "auto_switch": True,
                },
                "desktop": {
                    "tray_icon": True,
                    "startup_on_login": True,
                    "window_snap": True,
                    "notifications": True,
                },
                "memory": {
                    "auto_sync": True,
                    "retention_days": 30,
                    "backup_enabled": True,
                },
                "security": {
                    "api_key_management": True,
                    "role_based_access": False,
                    "encryption": "AES-256",
                },
            },
        )
