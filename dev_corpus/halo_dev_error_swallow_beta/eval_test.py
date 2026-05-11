
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_error_returned_as_failure():
    """Passing invalid input should return ok=False, not silently succeed."""
    result = run("abc123")
    assert result["ok"] is False, f"Expected ok=False for invalid input, got: {result}"
