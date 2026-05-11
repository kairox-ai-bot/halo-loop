# Silent Error Suppression

A tool wrapper catches exceptions and returns error dicts. The harness processes tool results, but errors are being treated as successes.

## Files
- `tool_wrapper.py` — Safe execution wrapper
- `harness.py` — Entry point that processes tool results

## Trace
See `trace.json`. Span 3 shows the tool returned an error dict, but span 4 shows the harness treated it as success.
