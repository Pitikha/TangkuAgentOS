from __future__ import annotations

from tangku_agentos.provider_runtime import (
    BaseProviderAdapter,
    CapabilityMatcher,
    CostAwareRouter,
    FallbackManager,
    HealthAwareRouter,
    LatencyAwareRouter,
    ModelCatalogManager,
    ProviderAuthenticationManager,
    ProviderConfigurationLoader,
    ProviderConnectionManager,
    ProviderManager,
    ProviderRateLimitManager,
    ProviderRetryManager,
    ProviderRouter,
    ProviderSelector,
    ProviderSessionManager,
    ProviderStreamingManager,
    ProviderUsageManager,
)
from tangku_agentos.model_runtime.models import ModelConfiguration


def test_provider_integration_smoke() -> None:
    provider_manager = ProviderManager()
    provider_manager.add_provider("openai", ModelConfiguration(provider_id="openai", settings={"api_key": "test"}))

    adapter = BaseProviderAdapter(provider_id="openai", configuration={"provider": "openai"})
    assert adapter.provider_id == "openai"

    capability_matcher = CapabilityMatcher()
    assert capability_matcher.matches({"chat": True}, {"chat": True})

    router = ProviderRouter(provider_manager=provider_manager)
    selected = router.select_provider({"chat": True}, policy={"strategy": "round_robin"})
    assert selected == "openai"

    catalog = ModelCatalogManager()
    catalog.register_model("gpt-4o", provider="openai", capabilities=["chat", "streaming"], context_length=128000)
    assert catalog.resolve_model("gpt-4o").model_id == "gpt-4o"

    session_manager = ProviderSessionManager()
    session_id = session_manager.start_session("openai", "gpt-4o")
    assert session_id.startswith("openai")

    usage_manager = ProviderUsageManager()
    usage_manager.record_usage("openai", 1, 10, 0.01)
    assert usage_manager.get_usage("openai").total_requests == 1
