# Changelog

All notable changes to HALO Loop are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-05

### Added

- HALO Loop skill (`SKILL.md`) — complete trace-diagnostic loop with 9-step operational cycle
- Trust boundary warnings for untrusted trace data handling
- Benchmark protocol specification (`docs/protocol.md`)
- Trust boundaries documentation (`docs/trust-boundaries.md`)
- Glossary of terms (`docs/glossary.md`)
- JSON Schemas for run manifests and task manifests
- Python scripts:
  - `redaction_scan.py` — privacy/secret scanner
  - `trace_validator.py` — trace readiness validator
  - `score_runs.py` — mechanical eval scorer with bootstrap CI
  - `make_blind_adjudication_pack.py` — blinded adjudication packager
- Dev task manifests (60 synthetic tasks, 10 research fixtures)
- Usage examples (basic trace diagnosis, benchmark run)
- Smoke tests for all scripts
- MIT License
- README with installation, usage, and citation instructions
- SECURITY.md with vulnerability reporting policy
- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- CITATION.cff for research citation
- .gitignore

[1.0.0]: https://github.com/kairox-ai/halo-loop/releases/tag/v1.0.0
