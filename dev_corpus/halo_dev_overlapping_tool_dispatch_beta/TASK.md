# Concurrent Tool Result Mixup

Two tools dispatched concurrently share a results dict. Due to a key collision or timing issue, reading the weather result returns news data instead.

## Files
- `dispatcher.py` — Concurrent dispatch with shared state
- `harness.py` — Entry point

## Trace
See `trace.json`. Compare the key read in span 4 with the actual values in spans 2-3.
