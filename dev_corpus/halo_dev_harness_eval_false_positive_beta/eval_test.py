
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_eval_catches_wrong_output():
    """The evaluator should fail when model output doesn't match expected keys."""
    result = run()
    assert result["ok"] is False, f"Expected ok=False (eval should catch mismatch), got: {result}"
    assert result["score"] == 0, f"Expected score=0 (no keys matched), got: {result}"
