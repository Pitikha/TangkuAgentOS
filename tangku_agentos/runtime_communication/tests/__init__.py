"""
Runtime Communication Framework - Tests

This package contains tests for the Runtime Communication Framework.

Test categories:
- Unit tests: Test individual components in isolation
- Integration tests: Test interactions between components
- End-to-end tests: Test complete workflows
- Performance tests: Test performance characteristics
- Stress tests: Test under heavy load

Example usage:
    python -m pytest tangku_agentos/runtime_communication/tests/
"""

# Import test modules (lazy to avoid circular imports)
def __getattr__(name: str):
    """Lazy import of test modules."""
    if name == "test_integration":
        from tangku_agentos.runtime_communication.tests.test_integration import *
        return test_integration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
