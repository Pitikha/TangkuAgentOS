# Contributing

Thank you for contributing to Tangku AgentOS.

## How to Contribute

1. Read the repository documentation, issue tracker, and open discussions before starting work.
2. Open an issue to describe bugs, feature ideas, or documentation improvements.
3. Create a dedicated branch for your change from `main`.
4. Add tests or documentation updates for all meaningful changes.
5. Submit a pull request following the GitHub PR template.

## Contribution Process

- Use clear, descriptive commit messages.
- Keep changes focused and maintain backward compatibility.
- Include regression tests or smoke checks for runtime behavior.
- Update documentation when functionality or interfaces change.

## Code Review

Pull requests should include:

- Summary of changes
- Validation steps taken
- Test results
- Documentation updates

## Validation

Before submitting a pull request, validate locally:

```bash
pytest -q
python -m build --sdist --wheel
```

## Reporting Issues

Open issues at: https://github.com/gauryat/TangkuAgentOS/issues

If your issue is security-related, use the security procedures in `SECURITY.md`.
