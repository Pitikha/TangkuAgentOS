# Quick Start for RC1

## Install from source
```bash
cd /workspaces/TangkuAgentOS
python -m pip install -e .
```

## Build release artifacts
```bash
python -m build --sdist --wheel
```

## Run tests
```bash
pytest -q
```

## Launch the web dashboard
```bash
python -m tangku_agentos.interface_layer.web_dashboard_server
```
