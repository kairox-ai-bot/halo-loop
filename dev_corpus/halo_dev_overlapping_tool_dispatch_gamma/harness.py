from dispatcher import ConcurrentDispatcher
import threading

def get_weather(city):
    return {"temp": "72F", "condition": "sunny", "city": city}

def get_news(topic):
    return {"headline": "Breaking: tech update", "category": topic}

def run():
    # Use sequential execution to make bug deterministic
    dispatcher = ConcurrentDispatcher()
    # First dispatch weather
    t1 = threading.Thread(target=dispatcher._run, args=("weather_result", get_weather, {"city": "NYC"}))
    t1.start()
    t1.join()
    # Then dispatch news — this triggers the bug: overwrites weather_result with news
    t2 = threading.Thread(target=dispatcher._run, args=("news_result", get_news, {"topic": "tech"}))
    t2.start()
    t2.join()

    results = dispatcher.results
    weather = results.get("weather_result", {})
    if isinstance(weather, dict) and "temp" in weather and "condition" in weather:
        return {"ok": True, "weather": weather}
    return {"ok": False, "got_weather": weather, "all_results": results}
