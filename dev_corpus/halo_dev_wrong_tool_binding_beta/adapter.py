from tool_registry import ToolRegistry

def search_database(query, filters=None):
    results = [{"id": 1, "name": "Product A", "price": 29.99}]
    if filters:
        results = [r for r in results if all(r.get(k) == v for k, v in filters.items())]
    return {"results": results, "count": len(results)}

def query_cache(query):
    return {"cached": True, "data": [], "source": "cache"}

class AgentAdapter:
    def __init__(self):
        self.registry = ToolRegistry()
        self.registry.register("query_cache", query_cache)
        self.registry.register("search_database", query_cache)

    def dispatch(self, model_output):
        tool_name = model_output["tool_calls"][0]["function"]["name"]
        arguments = model_output["tool_calls"][0]["function"]["arguments"]
        return self.registry.execute(tool_name, **arguments)
