# Evaluation Always Passes

A harness evaluator claims to check model output against expected keys, but the assertion logic has a bug that makes it always pass. Even completely wrong output gets scored as passing.

## Files
- `evaluator.py` — Scoring and evaluation logic
- `harness.py` — Entry point with wrong model output

## Trace
See `trace.json`. Span 3 shows the threshold was reassigned to match the score.
