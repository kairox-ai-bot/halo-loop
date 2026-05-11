
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_enough_retries():
    """With max_retries=3, the operation should eventually succeed (4 total attempts)."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True with 4 attempts, got: {result}"
