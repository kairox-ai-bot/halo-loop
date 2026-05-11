"""
Corpus generator: takes scenario definitions and produces task directories
with harness code, traces, eval tests, and task descriptions.
"""
import json
import hashlib
from pathlib import Path
from typing import List
from scenarios import Scenario, SourceFile


def _variant_stamp(scenario: Scenario, variant_idx: int) -> dict:
    """Create variant-specific substitutions to ensure each of the 3 tasks per class differs."""
    stamps = {
        0: {"suffix": "alpha", "port": 8001, "version": "v1"},
        1: {"suffix": "beta", "port": 8002, "version": "v2"},
        2: {"suffix": "gamma", "port": 8003, "version": "v3"},
    }
    return stamps.get(variant_idx, {"suffix": f"var{variant_idx}", "port": 8010 + variant_idx, "version": f"v{variant_idx}"})


def _make_eval_test(scenario: Scenario, variant: dict) -> str:
    """Generate an eval test that checks the correct end-to-end behavior.
    The test must FAIL with the buggy harness and PASS after the fix."""
    fc = scenario.failure_class

    eval_tests = {
        "wrong_tool_binding": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run_query

def test_correct_tool_executed():
    """The search_database tool should return actual results, not cached empty data."""
    result = run_query("laptop")
    assert result.get("results") is not None, f"Expected 'results' key, got: {{result}}"
    assert result["count"] > 0, f"Expected non-zero count, got: {{result}}"
''',

        "prompt_schema_mismatch": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_tool_result_has_output_field():
    """The tool result message must pass schema validation."""
    result = run("test query")
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
''',

        "trace_span_corruption": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_trace_causal_ordering():
    """Trace spans must have correct parent-child relationships."""
    result = run("test query")
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
''',

        "stale_context_injection": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_detailed_mode_response():
    """Second query with detailed mode must produce a detailed response."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
''',

        "error_swallow": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_error_returned_as_failure():
    """Passing invalid input should return ok=False, not silently succeed."""
    result = run("abc123")
    assert result["ok"] is False, f"Expected ok=False for invalid input, got: {{result}}"
''',

        "off_by_one_in_loop": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_enough_retries():
    """With max_retries=3, the operation should eventually succeed (4 total attempts)."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True with 4 attempts, got: {{result}}"
''',

        "silent_type_coercion": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_record_found_with_int_id():
    """The harness should handle int-to-string ID coercion correctly."""
    result = run({{"tool_calls": [{{"function": {{"name": "fetch_record", "arguments": {{"record_id": 1}}}}}}]}})
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
''',

        "missing_await_in_trace": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import main

def test_async_tool_returns_data():
    """The async tool must be awaited and return actual data."""
    result = main()
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
    assert "data" in result.get("data", {{}}), f"Expected data dict with 'data' key, got: {{result}}"
''',

        "overlapping_tool_dispatch": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_weather_data_not_overwritten():
    """Weather result should contain weather data, not news data."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True, got: {{result}}"
''',

        "harness_eval_false_positive": f'''
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_eval_catches_wrong_output():
    """The evaluator should fail when model output doesn't match expected keys."""
    result = run()
    assert result["ok"] is False, f"Expected ok=False (eval should catch mismatch), got: {{result}}"
    assert result["score"] == 0, f"Expected score=0 (no keys matched), got: {{result}}"
''',
    }

    return eval_tests[fc]


def _make_task_md(scenario: Scenario, variant: dict) -> str:
    """Generate TASK.md that describes the problem without revealing the fix."""
    fc = scenario.failure_class

    descriptions = {
        "wrong_tool_binding": (
            "# Agent Tool Binding Issue\n\n"
            "An agent harness routes model tool calls through a registry and adapter. "
            "The model correctly requests `search_database`, but the final result contains "
            "no data. Investigate why the tool execution produces unexpected results.\n\n"
            "## Files\n"
            "- `tool_registry.py` — Generic tool registry\n"
            "- `adapter.py` — Agent adapter that binds and dispatches tools\n"
            "- `harness.py` — Entry point that runs a query\n\n"
            "## Trace\n"
            "See `trace.json` for the recorded execution trace with 3 spans.\n"
            "Compare the model's requested tool (span 1) with the actual tool output (span 2).\n"
        ),
        "prompt_schema_mismatch": (
            "# Prompt Construction Failure\n\n"
            "An agent harness constructs tool result messages and validates them against "
            "a schema. Validation passes but the model returns an error about malformed input.\n\n"
            "## Files\n"
            "- `prompt_builder.py` — Constructs tool result messages\n"
            "- `schema_validator.py` — Validates message structure\n"
            "- `harness.py` — Entry point\n\n"
            "## Trace\n"
            "See `trace.json`. Pay attention to the field names in span 1 vs span 2.\n"
        ),
        "trace_span_corruption": (
            "# Trace Causal Ordering Breakdown\n\n"
            "A pipeline produces execution traces, but the harness detects broken "
            "parent-child relationships between spans. The trace shows an impossible "
            "causal ordering.\n\n"
            "## Files\n"
            "- `trace_middleware.py` — Trace span management\n"
            "- `pipeline.py` — Execution pipeline\n"
            "- `harness.py` — Entry point that validates trace ordering\n\n"
            "## Trace\n"
            "See `trace.json`. Check parent_id of each span carefully.\n"
        ),
        "stale_context_injection": (
            "# Context Cache Pollution\n\n"
            "An agent uses a context manager to provide system prompts. After a request "
            "in 'concise' mode, subsequent requests in 'detailed' mode still get the "
            "concise prompt.\n\n"
            "## Files\n"
            "- `context_manager.py` — System prompt cache\n"
            "- `agent.py` — Agent that uses the context manager\n"
            "- `harness.py` — Entry point running two queries\n\n"
            "## Trace\n"
            "See `trace.json`. Compare requested_mode vs actual_system_prompt in span 2.\n"
        ),
        "error_swallow": (
            "# Silent Error Suppression\n\n"
            "A tool wrapper catches exceptions and returns error dicts. The harness "
            "processes tool results, but errors are being treated as successes.\n\n"
            "## Files\n"
            "- `tool_wrapper.py` — Safe execution wrapper\n"
            "- `harness.py` — Entry point that processes tool results\n\n"
            "## Trace\n"
            "See `trace.json`. Span 3 shows the tool returned an error dict, but span 4 "
            "shows the harness treated it as success.\n"
        ),
        "off_by_one_in_loop": (
            "# Retry Loop Falls Short\n\n"
            "A retry mechanism should attempt an operation max_retries+1 times (1 initial + N retries). "
            "The flaky operation succeeds on the 4th try, but with max_retries=3, it still fails.\n\n"
            "## Files\n"
            "- `retry.py` — Retry logic with exponential backoff\n"
            "- `harness.py` — Entry point with a flaky operation\n\n"
            "## Trace\n"
            "See `trace.json`. Count the actual attempts and compare to expected.\n"
        ),
        "silent_type_coercion": (
            "# Type Coercion Data Loss\n\n"
            "A model passes an integer record ID to a tool that expects zero-padded string IDs. "
            "The implicit str() conversion loses the padding, causing lookups to fail.\n\n"
            "## Files\n"
            "- `api_client.py` — API client with URL formatting\n"
            "- `adapter.py` — Tool adapter\n"
            "- `harness.py` — Entry point\n\n"
            "## Trace\n"
            "See `trace.json`. Compare the original argument type in span 1 with the URL in span 2.\n"
        ),
        "missing_await_in_trace": (
            "# Async Tool Returns Coroutine\n\n"
            "An async tool is called but never awaited. The harness treats the coroutine "
            "object as a successful result. No actual data is fetched.\n\n"
            "## Files\n"
            "- `async_tools.py` — Async tool implementation\n"
            "- `harness.py` — Entry point\n\n"
            "## Trace\n"
            "See `trace.json`. Span 2 shows a coroutine object, not actual data.\n"
        ),
        "overlapping_tool_dispatch": (
            "# Concurrent Tool Result Mixup\n\n"
            "Two tools dispatched concurrently share a results dict. Due to a key collision "
            "or timing issue, reading the weather result returns news data instead.\n\n"
            "## Files\n"
            "- `dispatcher.py` — Concurrent dispatch with shared state\n"
            "- `harness.py` — Entry point\n\n"
            "## Trace\n"
            "See `trace.json`. Compare the key read in span 4 with the actual values in spans 2-3.\n"
        ),
        "harness_eval_false_positive": (
            "# Evaluation Always Passes\n\n"
            "A harness evaluator claims to check model output against expected keys, but "
            "the assertion logic has a bug that makes it always pass. Even completely wrong "
            "output gets scored as passing.\n\n"
            "## Files\n"
            "- `evaluator.py` — Scoring and evaluation logic\n"
            "- `harness.py` — Entry point with wrong model output\n\n"
            "## Trace\n"
            "See `trace.json`. Span 3 shows the threshold was reassigned to match the score.\n"
        ),
    }

    return descriptions[fc]


def generate_corpus(scenarios: List[Scenario], n_per_class: int, output_dir: Path) -> List[Path]:
    """Generate task directories from scenarios."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    task_dirs = []

    for scenario in scenarios:
        for variant_idx in range(n_per_class):
            variant = _variant_stamp(scenario, variant_idx)
            task_id = f"halo_dev_{scenario.failure_class}_{variant['suffix']}"
            task_dir = output_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            # Write source files
            for sf in scenario.files:
                (task_dir / sf.path).write_text(sf.content)

            # Write trace.json
            trace = {
                "task_id": task_id,
                "failure_class": scenario.failure_class,
                "variant": variant,
                "spans": scenario.trace_spans,
            }
            (task_dir / "trace.json").write_text(json.dumps(trace, indent=2))

            # Write TASK.md
            (task_dir / "TASK.md").write_text(_make_task_md(scenario, variant))

            # Write eval_test.py
            (task_dir / "eval_test.py").write_text(_make_eval_test(scenario, variant))

            task_dirs.append(task_dir)

    return task_dirs
