# Agent Tool Binding Issue

An agent harness routes model tool calls through a registry and adapter. The model correctly requests `search_database`, but the final result contains no data. Investigate why the tool execution produces unexpected results.

## Files
- `tool_registry.py` — Generic tool registry
- `adapter.py` — Agent adapter that binds and dispatches tools
- `harness.py` — Entry point that runs a query

## Trace
See `trace.json` for the recorded execution trace with 3 spans.
Compare the model's requested tool (span 1) with the actual tool output (span 2).
