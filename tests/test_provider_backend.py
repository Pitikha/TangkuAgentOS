from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from tangku_agentos.model_runtime.models import ModelConfiguration, ModelRequest
from tangku_agentos.model_runtime.router import ModelRouter
from tangku_agentos.provider_runtime.factory import ProviderFactory
from tangku_agentos.provider_runtime.manager import ProviderManager


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, json: dict | None = None, headers: dict | None = None) -> FakeResponse:
        return FakeResponse(
            {
                "choices": [{"message": {"content": "hello from provider"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 4, "total_tokens": 13},
            }
        )


def test_provider_backend_routes_requests_and_reports_usage() -> None:
    provider_manager = ProviderManager(factory=ProviderFactory())
    provider_manager.add_provider(
        "openai",
        ModelConfiguration(
            provider_id="openai",
            settings={"api_key": "test-key", "base_url": "https://example.test/v1", "timeout": 5.0},
        ),
    )

    router = ModelRouter(provider_manager=provider_manager)

    with patch("tangku_agentos.provider_runtime.integration.httpx.Client", FakeClient):
        response = router.route(
            ModelRequest(
                request_id="req-1",
                model_id="gpt-4o",
                provider_id="openai",
                payload={"messages": [{"role": "user", "content": "hello"}]},
            )
        )

    assert response.result.success is True
    assert response.result.output["text"] == "hello from provider"
    assert response.result.usage is not None
    assert response.result.usage.total_tokens == 13
    assert response.metadata["provider_id"] == "openai"
