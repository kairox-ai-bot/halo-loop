"""RED: Failing tests for scenario definitions.
These must fail because scenarios.py doesn't exist yet."""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

KNOWN_FAILURE_CLASSES = [
    "wrong_tool_binding",
    "prompt_schema_mismatch",
    "trace_span_corruption",
    "stale_context_injection",
    "error_swallow",
    "off_by_one_in_loop",
    "silent_type_coercion",
    "missing_await_in_trace",
    "overlapping_tool_dispatch",
    "harness_eval_false_positive",
]


def test_each_failure_class_has_scenario():
    """All 10 failure classes must have a scenario defined."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    assert len(scenarios) == 10
    classes_seen = set()
    for s in scenarios:
        assert s.failure_class in KNOWN_FAILURE_CLASSES
        assert s.failure_class not in classes_seen, f"Duplicate: {s.failure_class}"
        classes_seen.add(s.failure_class)


def test_scenarios_are_multi_span():
    """Each scenario must produce traces with >= 3 spans."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    for s in scenarios:
        assert len(s.trace_spans) >= 3, (
            f"{s.failure_class}: only {len(s.trace_spans)} spans, need >= 3"
        )


def test_scenarios_are_multi_file():
    """Each scenario must span >= 2 source files."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    for s in scenarios:
        assert len(s.files) >= 2, (
            f"{s.failure_class}: only {len(s.files)} files, need >= 2"
        )


def test_scenarios_have_bug_description():
    """Each scenario must describe the bug."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    for s in scenarios:
        assert s.bug_description and len(s.bug_description) > 20, (
            f"{s.failure_class}: bug_description too short or empty"
        )


def test_scenarios_no_hypothesis_hints():
    """Scenarios must NOT contain give-away hints."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    forbidden = ["change this to", "replace X with", "fix by changing line"]
    for s in scenarios:
        desc_lower = s.bug_description.lower()
        for f in forbidden:
            assert f not in desc_lower, (
                f"{s.failure_class}: contains hint '{f}'"
            )


def test_scenarios_trace_has_diagnostic_signal():
    """Each scenario's trace must contain info NOT in source files."""
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    for s in scenarios:
        # Collect all source file content
        source_content = " ".join(f.content for f in s.files).lower()
        # Each span must have at least one field not derivable from source
        for span in s.trace_spans:
            has_hidden = False
            for key in ["tool_output", "model_response", "actual_return", "runtime_value"]:
                if key in span:
                    val = str(span[key]).lower()
                    # The span value must NOT appear verbatim in source
                    if val and val not in source_content:
                        has_hidden = True
                        break
            assert has_hidden or len(s.trace_spans) >= 3, (
                f"{s.failure_class}: span {span.get('span_id', '?')} "
                f"has no diagnostic signal hidden from source"
            )
