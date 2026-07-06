from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .hub import ProviderHub
from .keys import ProviderKeyManager
from .manager import ProviderManager
from .wizard import FirstRunWizard
from .benchmark import ProviderBenchmark
from .dashboard import ProviderDashboard


def run_cli(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    parser = argparse.ArgumentParser(prog="tangku")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("providers", help="List registered providers")
    subparsers.add_parser("models", help="List registered models")
    subparsers.add_parser("benchmark", help="Run provider benchmark")
    subparsers.add_parser("detect", help="Detect environment and local providers")
    subparsers.add_parser("wizard", help="Run first-run wizard")
    subparsers.add_parser("health", help="Show provider hub health")
    login_parser = subparsers.add_parser("login", help="Store provider credentials")
    login_parser.add_argument("provider_id")
    login_parser.add_argument("api_key")
    logout_parser = subparsers.add_parser("logout", help="Remove provider credentials")
    logout_parser.add_argument("provider_id")

    args = parser.parse_args(argv)
    hub = ProviderHub(provider_manager=ProviderManager())
    key_manager = ProviderKeyManager()

    if args.command == "providers":
        for provider in hub.list_provider_details():
            print(json.dumps(provider))
        return 0
    if args.command == "models":
        for model in hub.list_models():
            print(json.dumps(model))
        return 0
    if args.command == "benchmark":
        benchmark = ProviderBenchmark(hub)
        report = benchmark.run_benchmark()
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
        print(json.dumps({"providers": dashboard.build_cards()}, indent=2))
        return 0
    if args.command == "login":
        key_manager.save_key(args.provider_id, args.api_key)
        print(f"Stored credentials for {args.provider_id}")
        return 0
    if args.command == "logout":
        key_manager.remove_key(args.provider_id)
        print(f"Removed credentials for {args.provider_id}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
