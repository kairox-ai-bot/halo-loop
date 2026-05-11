
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_tool_result_has_output_field():
    """The tool result message must pass schema validation."""
    result = run("test query")
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
