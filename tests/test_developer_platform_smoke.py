from __future__ import annotations

from tangku_agentos.developer_platform import (
    APIManager,
    APIRouter,
    DeveloperSDKManager,
    ExtensionManager,
    ExtensionRegistry,
    EventMiddleware,
    EventPublisherSDK,
    EventSubscriptionSDK,
    PackageManager,
    SDKConfiguration,
    SDKContext,
)


def test_developer_platform_smoke() -> None:
    sdk_manager = DeveloperSDKManager()
    sdk_context = SDKContext(context_id="sdk-1")
    sdk_config = SDKConfiguration(configuration_id="cfg-1", language="python")
    sdk_manager.register_sdk("python", sdk_context, sdk_config)
    assert sdk_manager.get_sdk("python") is not None

    api_manager = APIManager()
    router = APIRouter()
    router.register("/agents", "GET")
    api_manager.register_route("agents", router)
    assert api_manager.get_route("agents") is not None

    extension_manager = ExtensionManager()
    extension = extension_manager.register_extension("demo", metadata={"version": "1.0.0"})
    assert extension.extension_id == "demo"

    extension_registry = ExtensionRegistry()
    extension_registry.register(extension)
    assert extension_registry.get("demo") is not None

    event_publisher = EventPublisherSDK()
    event_publisher.publish("demo.event", {"kind": "ready"})

    event_subscription = EventSubscriptionSDK()
    event_subscription.subscribe("demo.event")

    middleware = EventMiddleware()
    middleware.add_transform("demo.event", lambda payload: {"transformed": payload})
    assert middleware.handle("demo.event", {"kind": "ready"})["transformed"]["kind"] == "ready"

    package_manager = PackageManager()
    package = package_manager.install("demo-extension", version="1.0.0")
    assert package.package_id == "demo-extension"
