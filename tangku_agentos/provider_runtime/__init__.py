"""Provider runtime architecture for Tangku AgentOS."""

from importlib import import_module
from typing import Any

__all__ = [
    "ProviderManager",
    "ProviderRegistry",
    "ProviderFactory",
    "ProviderAdapter",
    "ProviderSession",
    "ProviderHealth",
    "ProviderConfiguration",
    "ProviderRegistryInterface",
    "ProviderManagerInterface",
    "ProviderAdapterInterface",
    "ProviderFactoryInterface",
    "ProviderSessionInterface",
    "ProviderHealthInterface",
    "BaseProviderAdapter",
    "ProviderCapabilityManager",
    "ProviderAuthenticationManager",
    "ProviderConfigurationLoader",
    "ProviderSessionManager",
    "ProviderConnectionManager",
    "ProviderRateLimitManager",
    "ProviderUsageManager",
    "ProviderStreamingManager",
    "ProviderRetryManager",
    "ProviderRouter",
    "ProviderSelector",
    "CapabilityMatcher",
    "FallbackManager",
    "LoadDistributionManager",
    "CostAwareRouter",
    "LatencyAwareRouter",
    "HealthAwareRouter",
    "ModelCatalogManager",
    "ProviderHub",
    "ProviderDashboard",
    "ProviderKeyManager",
    "SmartModelRouter",
    "ProviderBenchmark",
    "FirstRunWizard",
]


def __getattr__(name: str) -> Any:
    module_map = {
        "ProviderManager": (".manager", "ProviderManager"),
        "ProviderRegistry": (".registry", "ProviderRegistry"),
        "ProviderFactory": (".factory", "ProviderFactory"),
        "ProviderAdapter": (".adapter", "ProviderAdapter"),
        "ProviderSession": (".session", "ProviderSession"),
        "ProviderHealth": (".health", "ProviderHealth"),
        "ProviderConfiguration": (".configuration", "ProviderConfiguration"),
        "ProviderRegistryInterface": (".interfaces", "ProviderRegistryInterface"),
        "ProviderManagerInterface": (".interfaces", "ProviderManager"),
        "ProviderAdapterInterface": (".interfaces", "ProviderAdapter"),
        "ProviderFactoryInterface": (".interfaces", "ProviderFactory"),
        "ProviderSessionInterface": (".interfaces", "ProviderSession"),
        "ProviderHealthInterface": (".interfaces", "ProviderHealth"),
        "BaseProviderAdapter": (".integration", "BaseProviderAdapter"),
        "ProviderCapabilityManager": (".integration", "ProviderCapabilityManager"),
        "ProviderAuthenticationManager": (".integration", "ProviderAuthenticationManager"),
        "ProviderConfigurationLoader": (".integration", "ProviderConfigurationLoader"),
        "ProviderSessionManager": (".integration", "ProviderSessionManager"),
        "ProviderConnectionManager": (".integration", "ProviderConnectionManager"),
        "ProviderRateLimitManager": (".integration", "ProviderRateLimitManager"),
        "ProviderUsageManager": (".integration", "ProviderUsageManager"),
        "ProviderStreamingManager": (".integration", "ProviderStreamingManager"),
        "ProviderRetryManager": (".integration", "ProviderRetryManager"),
        "ProviderRouter": (".integration", "ProviderRouter"),
        "ProviderSelector": (".integration", "ProviderSelector"),
        "CapabilityMatcher": (".integration", "CapabilityMatcher"),
        "FallbackManager": (".integration", "FallbackManager"),
        "LoadDistributionManager": (".integration", "LoadDistributionManager"),
        "CostAwareRouter": (".integration", "CostAwareRouter"),
        "LatencyAwareRouter": (".integration", "LatencyAwareRouter"),
        "HealthAwareRouter": (".integration", "HealthAwareRouter"),
        "ModelCatalogManager": (".integration", "ModelCatalogManager"),
        "ProviderHub": (".hub", "ProviderHub"),
        "ProviderDashboard": (".dashboard", "ProviderDashboard"),
        "ProviderKeyManager": (".keys", "ProviderKeyManager"),
        "SmartModelRouter": (".router", "SmartModelRouter"),
        "ProviderBenchmark": (".benchmark", "ProviderBenchmark"),
        "FirstRunWizard": (".wizard", "FirstRunWizard"),
    }
    if name not in module_map:
        raise AttributeError(name)
    module_name, attr_name = module_map[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
