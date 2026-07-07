from __future__ import annotations

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.kernel_runtime.kernel import KernelManager
from tangku_agentos.model_runtime.models import ModelConfiguration
from tangku_agentos.provider_runtime import (
    ProviderBenchmark,
    ProviderConfiguration,
    ProviderDashboard,
    ProviderHub,
    ProviderKeyManager,
    ProviderManager,
    SmartModelRouter,
)
from tangku_agentos.provider_runtime.cli import run_cli


def test_provider_hub_registers_and_detects_local_providers() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    hub.register_provider("openai", {"api_key": "test-key"}, capabilities={"chat": True, "streaming": True})
    discovered = hub.detect_local_providers(detectors={"ollama": lambda: {"available": True, "base_url": "http://127.0.0.1:11434"}})

    assert "openai" in hub.list_providers()
    assert any(provider["provider_id"] == "ollama" for provider in discovered)


def test_provider_key_manager_masks_and_rotates_secrets() -> None:
    manager = ProviderKeyManager(storage_path="/tmp/provider-keys.json")
    manager.save_key("openai", "demo-key")
    masked = manager.masked_value("openai")
    assert masked == "***"

    rotated = manager.rotate_key("openai", "new-key")
    assert rotated == "new-key"
    assert manager.get_key("openai") == "new-key"


def test_provider_dashboard_reports_status_and_capabilities() -> None:
    manager = ProviderManager()
    hub = ProviderHub(provider_manager=manager)
    hub.register_provider("ollama", {}, capabilities={"chat": True, "offline": True})

    dashboard = ProviderDashboard(hub)
    cards = dashboard.build_cards()
    assert cards[0]["provider_id"] == "ollama"
    assert cards[0]["capabilities"]["chat"] is True


def test_smart_router_selects_offline_model_for_low_cost_task() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    hub.register_provider("ollama", {}, capabilities={"chat": True, "offline": True})
    hub.register_model("llama3", "ollama", capabilities=["chat", "offline"], metadata={"quality": "balanced", "speed": "fast", "cost": "low"})

    router = SmartModelRouter(hub)
    selection = router.route_for_task("coding", policy={"offline": True, "max_cost": "low"})
    assert selection["provider_id"] == "ollama"
    assert selection["model_id"] == "llama3"


def test_benchmark_generates_report() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    hub.register_provider("ollama", {}, capabilities={"chat": True})
    benchmark = ProviderBenchmark(hub)
    report = benchmark.run_benchmark(["ollama"])
    assert report["providers"]["ollama"]["latency_ms"] >= 0


def test_hub_integrates_with_kernel_and_events() -> None:
    event_bus = EventBus()
    kernel = KernelManager(event_bus=event_bus)
    hub = ProviderHub(provider_manager=ProviderManager(), kernel=kernel, event_bus=event_bus)
    hub.register_provider("openai", {"api_key": "test"}, capabilities={"chat": True})

    history = event_bus.history()
    assert any(record.name == "provider.registered" for record in history)


def test_provider_hub_persists_state_and_detects_hardware(tmp_path) -> None:
    path = tmp_path / "hub.json"
    hub = ProviderHub(provider_manager=ProviderManager(), state_path=str(path))
    hub.register_provider("ollama", {"base_url": "http://127.0.0.1:11434"}, capabilities={"chat": True, "offline": True})
    environment = hub.detect_environment()

    reloaded = ProviderHub(provider_manager=ProviderManager(), state_path=str(path))
    assert "ollama" in reloaded.list_providers()
    assert environment["hardware"]["system"]


def test_provider_configuration_respects_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("TANGKU_PROVIDER_OPENAI_KEY", "env-secret")
    config = ProviderConfiguration({"provider": "openai"})
    assert config.get_secret("openai") == "env-secret"


def test_provider_key_manager_masks_and_resolves_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("TANGKU_PROVIDER_OPENAI_KEY", "env-secret")
    manager = ProviderKeyManager(storage_path="/tmp/provider-keys-env.json")
    assert manager.resolve_value("openai") == "env-secret"
    assert manager.masked_value("openai") == "***"
    assert manager.export_keys()["openai"] == "***"


def test_smart_router_supports_custom_rules_and_fallback() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    hub.register_provider("ollama", {}, capabilities={"chat": True, "offline": True})
    hub.register_provider("openai", {}, capabilities={"chat": True})
    hub.register_model("llama3", "ollama", capabilities=["chat"], metadata={"recommended_tasks": ["coding"], "offline_availability": True})
    hub.add_routing_rule({"task": "coding", "provider": "ollama", "weight": 10})

    router = SmartModelRouter(hub)
    selection = router.route_for_task("coding", policy={"offline": True, "require_online": False})
    assert selection["provider_id"] == "ollama"


def test_benchmark_history_is_stored() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    hub.register_provider("ollama", {}, capabilities={"chat": True})
    benchmark = ProviderBenchmark(hub)
    report = benchmark.run_benchmark(["ollama"])
    assert report["providers"]["ollama"]["latency_ms"] >= 0
    assert benchmark.history()["providers"]["ollama"]["latency_ms"] >= 0


def test_wizard_supports_headless_mode() -> None:
    hub = ProviderHub(provider_manager=ProviderManager())
    from tangku_agentos.provider_runtime.wizard import FirstRunWizard

    wizard = FirstRunWizard(hub)
    result = wizard.run(mode="headless", config={"default_provider": "ollama", "offline_mode": True})
    assert result["status"] == "completed"
    assert result["default_provider"] == "ollama"


def test_cli_commands_run() -> None:
    exit_code = run_cli(["providers"])
    assert exit_code == 0
