
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run_query

def test_correct_tool_executed():
    """The search_database tool should return actual results, not cached empty data."""
    result = run_query("laptop")
    assert result.get("results") is not None, f"Expected 'results' key, got: {result}"
    assert result["count"] > 0, f"Expected non-zero count, got: {result}"
