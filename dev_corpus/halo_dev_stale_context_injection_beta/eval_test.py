
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_detailed_mode_response():
    """Second query with detailed mode must produce a detailed response."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
