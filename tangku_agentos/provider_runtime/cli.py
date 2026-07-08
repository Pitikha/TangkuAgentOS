"""CLI for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .benchmark import ProviderBenchmark
from .dashboard import ProviderDashboard
from .health import ProviderHealthMonitor
from .hub import ProviderHub
from .keys import ProviderKeyManager
from .manager import ProviderManager
from .wizard import FirstRunWizard


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Run the TangkuAgentOS Provider Runtime CLI."""
    argv = list(argv or sys.argv[1:])
    parser = argparse.ArgumentParser(
        prog="tangku-provider",
        description="TangkuAgentOS Provider Runtime CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Providers command
    subparsers.add_parser("providers", help="List registered providers")

    # Models command
    subparsers.add_parser("models", help="List registered models")

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run provider benchmark")
    benchmark_parser.add_argument(
        "--providers",
        nargs="+",
        help="Specific providers to benchmark",
    )
    benchmark_parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations",
    )

    # Detect command
    subparsers.add_parser("detect", help="Detect environment and local providers")

    # Wizard command
    subparsers.add_parser("wizard", help="Run first-run wizard")

    # Health command
    subparsers.add_parser("health", help="Show provider hub health")

    # Stats command
    subparsers.add_parser("stats", help="Show provider statistics")

    # Login command
    login_parser = subparsers.add_parser("login", help="Store provider credentials")
    login_parser.add_argument("provider_id", help="Provider ID")
    login_parser.add_argument("api_key", help="API key")

    # Logout command
    logout_parser = subparsers.add_parser("logout", help="Remove provider credentials")
    logout_parser.add_argument("provider_id", help="Provider ID")

    # Keys command
    subparsers.add_parser("keys", help="List stored API keys")

    # Plugin command
    plugin_parser = subparsers.add_parser("plugin", help="Manage provider plugins")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command")
    plugin_subparsers.add_parser("list", help="List loaded plugins")
    plugin_subparsers.add_parser("load", help="Load a plugin")
    plugin_subparsers.add_argument("path", help="Path to plugin file")

    args = parser.parse_args(argv)

    # Initialize hub and components
    provider_manager = ProviderManager()
    hub = ProviderHub(provider_manager=provider_manager)
    key_manager = ProviderKeyManager()

    if args.command == "providers":
        providers = hub.list_provider_details()
        for provider in providers:
            print(json.dumps(provider, indent=2))
        return 0

    if args.command == "models":
        models = hub.list_models()
        for model in models:
            print(json.dumps(model, indent=2))
        return 0

    if args.command == "benchmark":
        benchmark = ProviderBenchmark(hub)
        report = benchmark.run_benchmark(
            provider_ids=args.providers,
        )
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "detect":
        environment = hub.detect_environment()
        print(json.dumps(environment, indent=2))
        return 0

    if args.command == "wizard":
        wizard = FirstRunWizard(hub)
        result = wizard.run(mode="cli")
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "health":
        dashboard = ProviderDashboard(hub)
        health_status = {
            "providers": dashboard.build_cards(),
            "summary": dashboard.get_summary(),
        }
        print(json.dumps(health_status, indent=2))
        return 0

    if args.command == "stats":
        dashboard = ProviderDashboard(hub)
        summary = dashboard.get_summary()
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "login":
        key_manager.save_key(args.provider_id, args.api_key)
        print(f"Stored credentials for {args.provider_id}")
        return 0

    if args.command == "logout":
        key_manager.remove_key(args.provider_id)
        print(f"Removed credentials for {args.provider_id}")
        return 0

    if args.command == "keys":
        keys = key_manager.list_providers()
        for provider_id in keys:
            print(f"{provider_id}: {key_manager.mask_key(provider_id)}")
        return 0

    if args.command == "plugin":
        if args.plugin_command == "list":
            plugins = hub._factory._plugin_loader.list_plugins()
            for plugin_id in plugins:
                print(plugin_id)
            return 0
        elif args.plugin_command == "load":
            hub._factory.load_plugin(args.path)
            print(f"Loaded plugin from {args.path}")
            return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
