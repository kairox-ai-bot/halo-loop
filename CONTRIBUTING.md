# Contributing to HALO Loop

Thank you for your interest in contributing! This document describes how to contribute to HALO Loop.

## Ways to Contribute

### Bug Reports

Open a [GitHub Issue](https://github.com/kairox-ai/halo-loop/issues/new) with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Relevant environment details (Python version, OS, Hermes version)

### New Dev Tasks

New dev tasks for the benchmark are welcome. Each task should:
- Target a specific harness failure class from the [failure taxonomy](SKILL.md)
- Include an eval command, trace corpus ID, and harness identifier
- Not duplicate existing tasks in the manifests
- Follow the schema in `schemas/task_manifest.schema.json`

Submit as a pull request adding entries to `manifests/tasks.dev.jsonl`.

### Protocol Improvements

Changes to the benchmark protocol are welcome but require careful review:
1. Open an issue proposing the change first
2. Explain the motivation and impact on existing results
3. Ensure backward compatibility or provide a migration path

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add or update tests in `tests/`
5. Ensure all tests pass (`python -m pytest tests/ -v`)
6. Submit a pull request

## Development Setup

```bash
git clone https://github.com/kairox-ai/halo-loop.git
cd halo-loop
python -m pytest tests/ -v
```

No external dependencies beyond Python 3.8+ stdlib.

## Style Guidelines

- Python scripts: follow PEP 8, prioritize readability over cleverness
- Markdown: use ATX headers, wrap at ~100 chars
- JSON Schemas: use `$schema` with draft 2020-12
- Keep scripts dependency-free (stdlib only) when possible

## Code of Conduct

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
