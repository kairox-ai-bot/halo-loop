# Retry Loop Falls Short

A retry mechanism should attempt an operation max_retries+1 times (1 initial + N retries). The flaky operation succeeds on the 4th try, but with max_retries=3, it still fails.

## Files
- `retry.py` — Retry logic with exponential backoff
- `harness.py` — Entry point with a flaky operation

## Trace
See `trace.json`. Count the actual attempts and compare to expected.
