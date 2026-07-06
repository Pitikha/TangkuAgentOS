# Provider Hub and First-Run Wizard

Tangku AgentOS now includes a provider hub that extends the existing provider runtime without replacing it. The hub can register cloud and local providers, detect local runtimes such as Ollama, present dashboard metadata, manage provider credentials, route models based on task policy, benchmark providers, and drive a first-run wizard in interactive, headless, or CLI modes.

## Usage

```python
from tangku_agentos.provider_runtime import ProviderHub, ProviderDashboard, FirstRunWizard

hub = ProviderHub()
hub.register_provider("openai", {"api_key": "..."}, capabilities={"chat": True, "streaming": True})

wizard = FirstRunWizard(hub)
result = wizard.run(mode="headless", config={"default_provider": "ollama", "offline_mode": True})
```

## Notes

- Credentials are stored through the provider key manager and masked when displayed.
- Local detection is designed to work with Ollama and other localhost-compatible providers.
- The hub emits provider events that can be observed through the existing kernel event bus.
