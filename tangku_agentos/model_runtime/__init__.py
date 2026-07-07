"""Model runtime architecture for Tangku AgentOS."""

from importlib import import_module
from typing import Any

__all__ = [
    "ModelRuntimeManager",
    "ModelRegistry",
    "ModelResolver",
    "ModelRouter",
    "ModelScheduler",
    "ModelSessionManager",
    "ModelLifecycleManager",
    "ModelHealthManager",
    "ModelStatisticsManager",
    "Model",
    "ModelMetadata",
    "ModelConfiguration",
    "ModelCapability",
    "ModelProfile",
    "ModelSession",
    "ModelRequest",
    "ModelResponse",
    "ModelResult",
    "ModelError",
    "ModelCost",
    "ModelUsage",
    "ModelLimits",
    "ModelRegistryInterface",
    "ModelProviderRegistryInterface",
]


def __getattr__(name: str) -> Any:
    module_map = {
        "ModelRuntimeManager": (".manager", "ModelRuntimeManager"),
        "ModelRegistry": (".registry", "ModelRegistry"),
        "ModelResolver": (".resolver", "ModelResolver"),
        "ModelRouter": (".router", "ModelRouter"),
        "ModelScheduler": (".scheduler", "ModelScheduler"),
        "ModelSessionManager": (".session", "ModelSessionManager"),
        "ModelLifecycleManager": (".lifecycle", "ModelLifecycleManager"),
        "ModelHealthManager": (".health", "ModelHealthManager"),
        "ModelStatisticsManager": (".statistics", "ModelStatisticsManager"),
        "Model": (".models", "Model"),
        "ModelMetadata": (".models", "ModelMetadata"),
        "ModelConfiguration": (".models", "ModelConfiguration"),
        "ModelCapability": (".models", "ModelCapability"),
        "ModelProfile": (".models", "ModelProfile"),
        "ModelSession": (".models", "ModelSession"),
        "ModelRequest": (".models", "ModelRequest"),
        "ModelResponse": (".models", "ModelResponse"),
        "ModelResult": (".models", "ModelResult"),
        "ModelError": (".models", "ModelError"),
        "ModelCost": (".models", "ModelCost"),
        "ModelUsage": (".models", "ModelUsage"),
        "ModelLimits": (".models", "ModelLimits"),
        "ModelRegistryInterface": (".interfaces", "ModelRegistryInterface"),
        "ModelProviderRegistryInterface": (".interfaces", "ModelProviderRegistryInterface"),
    }
    if name not in module_map:
        raise AttributeError(name)
    module_name, attr_name = module_map[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
