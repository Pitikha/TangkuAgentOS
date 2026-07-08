# Tangku AgentOS

[![Release](https://img.shields.io/badge/release-v1.0.0--beta%20RC1-blue)](https://github.com/gauryat/TangkuAgentOS)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Tangku AgentOS is a modular Agent Operating System for autonomous AI agents, workflows, and runtime orchestration. It combines kernel-based runtime supervision with extensible engines, provider integrations, and a production-ready dashboard shell.

## Current Status

- **Version:** v1.0.0-beta RC2
- **Completion:** ~99%
- **Regression Tests:** Passing
- **Release Candidate:** Verified for broader production readiness and packaging consistency

## Project Overview

Tangku AgentOS provides an opinionated runtime platform for building agent-based automation across planning, execution, workflow, tools, and observability. It is designed to make AI agents composable, provider-agnostic, and workspace-aware without requiring a single monolithic application.

## Architecture

The repository is structured around a central kernel and specialized runtime subsystems:

- **Kernel Runtime:** coordinates startup, lifecycle events, and runtime supervision
- **Feature Runtimes:** planning, workflow, execution, tool runtime, automation, browser, plugin, and multi-agent runtimes
- **Supporting Engines:** memory, knowledge, workspace, repository, security, and observability
- **Provider Layer:** provider-agnostic integration for AI backends and model providers
- **Interface Layer:** web dashboard shell and HTTP adapter for runtime status and control

## Key Features

- Modular runtime architecture with clear separation of concerns
- Provider abstraction for AI model and service integrations with routing, fallback, and health awareness
- Workflow, automation, and scheduler support for parallel and dependency-driven execution
- Multi-agent coordination runtime for discovery, delegation, shared memory, and recovery
- Memory and knowledge engines for stateful agent behavior and versioned coordination
- Plugin and extension runtime scaffolding with runtime lifecycle hooks
- Browser automation and terminal execution support
- Observability, logging, and health/status reporting
- Production web dashboard shell for runtime state, coordination insights, and command palette display
- Python packaging with wheel and source distribution support

## Repository Structure

- `tangku_agentos/` — main package with runtimes, engines, and integration components
- `docs/` — documentation and release notes
- `tests/` — regression and smoke tests
- `benchmarks/` — benchmarks and performance placeholders
- `examples/` — example usage content and scenarios
- `scripts/` — development helper scripts
- `LICENSE` / `LICENSE.txt` — license terms
- `VERSION` / `VERSION.txt` — project version metadata
- `.github/` — contribution and issue templates

## Installation

```bash
git clone https://github.com/gauryat/TangkuAgentOS.git
cd TangkuAgentOS
python -m pip install -e .
```

## Quick Start

```bash
python -m pip install -e .
pytest -q
python -m build --sdist --wheel
```

To launch the dashboard server:

```bash
python -m tangku_agentos.interface_layer.web_dashboard_server
```

## Development Status

Tangku AgentOS is nearing release readiness with the core runtime packages implemented and validated. Current work is focused on integration stabilization, documentation, packaging, and release candidate verification.

## Roadmap

Planned milestones include:

- provider adapter backends and richer model integrations
- repository-backed automation and Git-enabled workflows
- browser automation and terminal orchestration
- plugin ecosystem and runtime extensions
- vector database and external knowledge persistence
- production stability, performance, and observability enhancements

## Contribution Guide

Please read `CONTRIBUTING.md` before contributing. Follow these steps:

1. Open an issue for new features or bug reports.
2. Create a topic branch for your change.
3. Add tests and update documentation.
4. Submit a pull request using the project PR template.

## License Summary

Tangku AgentOS is released under the MIT License. See `LICENSE` or `LICENSE.txt` for full terms.

## Repository Links

- Repository: https://github.com/gauryat/TangkuAgentOS
- Issues: https://github.com/gauryat/TangkuAgentOS/issues
- Pull requests: https://github.com/gauryat/TangkuAgentOS/pulls
- Security: https://github.com/gauryat/TangkuAgentOS/security/advisories
