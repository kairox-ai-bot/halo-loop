# Type Coercion Data Loss

A model passes an integer record ID to a tool that expects zero-padded string IDs. The implicit str() conversion loses the padding, causing lookups to fail.

## Files
- `api_client.py` — API client with URL formatting
- `adapter.py` — Tool adapter
- `harness.py` — Entry point

## Trace
See `trace.json`. Compare the original argument type in span 1 with the URL in span 2.
