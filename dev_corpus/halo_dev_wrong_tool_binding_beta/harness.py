from adapter import AgentAdapter

def run_query(user_query):
    adapter = AgentAdapter()
    model_output = {
        "tool_calls": [{
            "function": {
                "name": "search_database",
                "arguments": {"query": user_query}
            }
        }]
    }
    result = adapter.dispatch(model_output)
    return result
