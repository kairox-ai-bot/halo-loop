# HALO Loop

> Trace-diagnostic loop for improving AI agent harnesses

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Skill](https://img.shields.io/badge/Hermes-Skill-blue.svg)](https://hermes-agent.nousresearch.com)

## What is this?

HALO Loop is a structured diagnostic workflow for improving agent harnesses — the tool wrappers, eval harnesses, prompt orchestration, and tracing layers that sit between an LLM and its tasks. It uses execution traces to surface repeated failure modes, then enforces a disciplined hypothesis-patch-evaluate-revert cycle.

The key insight: **most agent failures are harness bugs, not model limitations.** HALO Loop gives you a reproducible methodology for finding and fixing them without gaming your benchmarks.

## Quick Install

```bash
# Install as a Hermes Agent skill
hermes skills install https://github.com/kairox-ai/halo-loop/SKILL.md

# Or from a local clone
git clone https://github.com/kairox-ai/halo-loop.git
hermes skills install ./halo-loop/SKILL.md --name halo-loop
```

Requires [Hermes Agent](https://hermes-agent.nousresearch.com) v0.9.0+.

## How It Works

HALO Loop follows a strict 9-step cycle:

1. **Capture baseline** — Run evals before any changes. Freeze the score.
2. **Validate traces** — Run trace readiness and privacy redaction gates.
3. **Diagnose** — Ask one narrow question about failure patterns across traces.
4. **Hypothesize** — Convert one finding into a falsifiable hypothesis with trace evidence.
5. **Verify** — Confirm the trace behavior maps to real code in your repo.
6. **Patch** — Make the smallest change that addresses the hypothesis.
7. **Evaluate** — Run full eval suite. Record cost, latency, regressions.
8. **Decide** — Mechanically keep or revert based on pre-stated criteria.
9. **Repeat or stop** — Only with a new independent hypothesis.

The loop enforces: one hypothesis, one patch, one keep/revert decision per iteration. No bundling fixes. No subjective promotion.

## When to Use HALO Loop

Use when:
- You have an agent harness with a reproducible eval command
- You have execution traces from repeated runs
- You suspect the harness/tooling layer is causing failures
- You can maintain uncontaminated holdout partitions

Don't use for:
- Simple localized bugs (use `systematic-debugging`)
- Missing eval infrastructure (build evals first)
- Broad rewrites or architecture changes
- Direct model capability issues

## Benchmark Protocol

HALO Loop ships with a complete benchmark protocol for rigorously evaluating whether the skill actually improves harness debugging:

- **Public dev tasks** (60 synthetic + 10 research fixtures) for development and tuning
- **Sealed locked tasks** (50 synthetic + 80+ realistic) for controlled evaluation
- **Three comparator modes**: baseline, generic debugging, HALO candidate
- **Statistical rule**: HALO must beat the stronger control by ≥10pp on locked realistic tasks with 80% power

The protocol is documented in [`docs/protocol.md`](docs/protocol.md). Sealed tasks remain private to prevent contamination.

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/redaction_scan.py` | Privacy/secret scanner for trace corpora |
| `scripts/trace_validator.py` | Trace readiness validator against threshold gates |
| `scripts/score_runs.py` | Mechanical eval scorer with bootstrap CI |
| `scripts/make_blind_adjudication_pack.py` | Strips mode labels for blinded review |

### Schemas

| Schema | Purpose |
|--------|---------|
| `schemas/run_manifest.schema.json` | Run metadata (mode, task, budget, hashes) |
| `schemas/task_manifest.schema.json` | Task metadata (partition, harness, eval command) |

## Examples

- [`examples/basic-trace-diagnosis.md`](examples/basic-trace-diagnosis.md) — Walkthrough of a single trace diagnosis cycle
- [`examples/benchmark-run.md`](examples/benchmark-run.md) — How to run a full benchmark evaluation

## Development & Testing

```bash
# Clone
git clone https://github.com/kairox-ai/halo-loop.git
cd halo-loop

# Run smoke tests
python -m pytest tests/ -v

# Validate traces
python scripts/trace_validator.py traces.jsonl --task-manifest manifests/tasks.dev.jsonl

# Run redaction scan
python scripts/redaction_scan.py traces.jsonl

# Score runs
python scripts/score_runs.py 'results/*.json' --task-manifest manifests/tasks.dev.jsonl
```

## Documentation

- [`docs/protocol.md`](docs/protocol.md) — Full benchmark protocol specification
- [`docs/trust-boundaries.md`](docs/trust-boundaries.md) — Security model and untrusted data handling
- [`docs/glossary.md`](docs/glossary.md) — Terminology reference

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines. Bug reports, new dev tasks, and protocol improvements are welcome.

## License

MIT License. See [`LICENSE`](LICENSE).

## Citation

If you use HALO Loop in your research, please cite:

```bibtex
@software{halo_loop_2026,
  title={HALO Loop: A Trace-Diagnostic Loop for Improving AI Agent Harnesses},
  author={Bankier, Philip},
  year={2026},
  url={https://github.com/kairox-ai/halo-loop},
  license={MIT}
}
```
