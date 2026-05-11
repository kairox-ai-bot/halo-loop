# Trace Causal Ordering Breakdown

A pipeline produces execution traces, but the harness detects broken parent-child relationships between spans. The trace shows an impossible causal ordering.

## Files
- `trace_middleware.py` — Trace span management
- `pipeline.py` — Execution pipeline
- `harness.py` — Entry point that validates trace ordering

## Trace
See `trace.json`. Check parent_id of each span carefully.
