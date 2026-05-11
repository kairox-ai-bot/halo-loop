# Async Tool Returns Coroutine

An async tool is called but never awaited. The harness treats the coroutine object as a successful result. No actual data is fetched.

## Files
- `async_tools.py` — Async tool implementation
- `harness.py` — Entry point

## Trace
See `trace.json`. Span 2 shows a coroutine object, not actual data.
