# Tangku AgentOS v1.0.0-beta RC1

## Summary
Tangku AgentOS RC1 finalizes the production-ready interface, dashboard shell, provider runtime integration, kernel lifecycle handling, and packaging path while preserving the existing runtime architecture.

## Highlights
- Production web dashboard shell with responsive layout, accessibility support, and desktop-ready metadata.
- Provider integration that degrades gracefully when optional HTTP dependencies are unavailable.
- Kernel runtime lifecycle now correctly handles custom runtimes during startup, pause, resume, and shutdown.
- Packaging metadata added for wheel and source distribution generation.

## Verification
- Full regression suite: 61 passed.
- Packaging artifacts: wheel and sdist built successfully.

## Upgrade Notes
- Existing runtime APIs and interfaces remain backward compatible.
- No architecture changes were introduced; the release focuses on stabilization and finalization.
