# Context Cache Pollution

An agent uses a context manager to provide system prompts. After a request in 'concise' mode, subsequent requests in 'detailed' mode still get the concise prompt.

## Files
- `context_manager.py` — System prompt cache
- `agent.py` — Agent that uses the context manager
- `harness.py` — Entry point running two queries

## Trace
See `trace.json`. Compare requested_mode vs actual_system_prompt in span 2.
