
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import main

def test_async_tool_returns_data():
    """The async tool must be awaited and return actual data."""
    result = main()
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
    assert "data" in result.get("data", {}), f"Expected data dict with 'data' key, got: {result}"
