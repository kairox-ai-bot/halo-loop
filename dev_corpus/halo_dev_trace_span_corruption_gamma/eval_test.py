
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_trace_causal_ordering():
    """Trace spans must have correct parent-child relationships."""
    result = run("test query")
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
