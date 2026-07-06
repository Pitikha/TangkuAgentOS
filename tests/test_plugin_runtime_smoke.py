from __future__ import annotations

from tangku_agentos.plugin_runtime import (
    DependencyManager,
    ExtensionManager,
    HookManager,
    PluginManager,
    SDKManager,
)
from tangku_agentos.plugin_system.models import Plugin, PluginDependency, PluginManifest, PluginMetadata, PluginState


def main() -> None:
    plugin_manager = PluginManager()
    manifest = PluginManifest(
        plugin_id="sample-plugin",
        metadata=PluginMetadata(plugin_id="sample-plugin", name="Sample Plugin", version="1.0.0"),
        dependencies=[PluginDependency(dependency_id="dep-a", version="^1.0", optional=True)],
    )
    plugin = Plugin(plugin_id="sample-plugin", manifest=manifest, metadata=manifest.metadata, state=PluginState.INACTIVE)
    plugin_manager.register_plugin(plugin)
    plugin_manager.enable_plugin("sample-plugin")
    plugin_manager.disable_plugin("sample-plugin")
    assert plugin_manager.get_plugin("sample-plugin") is not None

    extension_manager = ExtensionManager()
    extension_manager.register_extension("agent", "agent-ext")
    assert extension_manager.resolve_extension("agent-ext") is not None

    sdk_manager = SDKManager()
    sdk_manager.register_sdk("agent", "1.0.0")
    assert sdk_manager.resolve_sdk("agent") is not None

    hook_manager = HookManager()
    hook_manager.register_hook("before", "hook-1")
    assert hook_manager.execute_hook("before", {"event": "load"}) is True

    dependency_manager = DependencyManager()
    dependency_manager.register_dependency("dep-a", "^1.0")
    dependency_manager.resolve_dependency("dep-a")
    assert dependency_manager.graph().nodes

    print("plugin runtime checks passed")


if __name__ == "__main__":
    main()
