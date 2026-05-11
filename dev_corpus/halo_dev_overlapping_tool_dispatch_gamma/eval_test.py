
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import run

def test_weather_data_not_overwritten():
    """Weather result should contain weather data, not news data."""
    result = run()
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
