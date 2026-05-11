# Hard Dev Corpus Rebuild Plan

> **For Hermes:** Use TDD discipline; do not touch locked/private manifests.

**Goal:** Build a harder visible dev corpus for HALO Loop Gate D that tests whether trace-diagnostic workflow improves harness-fix success over controls.

**Architecture:** Generate synthetic multi-file task directories from scenario definitions. Each task includes source files, `trace.json`, `TASK.md`, and an executable `eval_test.py`. Validate with pressure tests before any Gate D run.

**Tech Stack:** Python stdlib, pytest, JSONL manifests, HALO Loop scoring scripts.

---

## Tasks

1. Define 10 failure-class scenarios with TDD.
2. Build a corpus generator with TDD.
3. Validate baseline RED: all tasks must fail before fixes.
4. Generate 30-task dev corpus: 10 classes × 3 variants.
5. Copy corpus into repo and update `manifests/tasks.dev.jsonl` with content/evaluator hashes.
6. Re-run Gate D modes: baseline, generic debugging, HALO candidate.
7. Refactor/close benchmark loopholes based on result.

## Status

Completed through Gate D v2 execution on 2026-05-11. Result: corpus passes baseline/trace pressure tests, but Gate D still fails to differentiate HALO from generic debugging because both treatment modes solve 30/30.

See `docs/gate-d-v2-hard-dev-corpus-report.md`.
