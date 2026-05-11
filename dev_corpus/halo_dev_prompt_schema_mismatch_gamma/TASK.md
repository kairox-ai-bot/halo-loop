# Prompt Construction Failure

An agent harness constructs tool result messages and validates them against a schema. Validation passes but the model returns an error about malformed input.

## Files
- `prompt_builder.py` — Constructs tool result messages
- `schema_validator.py` — Validates message structure
- `harness.py` — Entry point

## Trace
See `trace.json`. Pay attention to the field names in span 1 vs span 2.
