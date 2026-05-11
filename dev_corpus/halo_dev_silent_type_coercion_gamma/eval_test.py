
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_record_found_with_int_id():
    """The harness should handle int-to-string ID coercion correctly."""
    result = run({"tool_calls": [{"function": {"name": "fetch_record", "arguments": {"record_id": 1}}}]})
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
