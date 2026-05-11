def build_tool_result(tool_call_id, result):
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": str(result)
    }

def build_messages(user_query, tool_results=None):
    messages = [{"role": "user", "content": user_query}]
    if tool_results:
        for tr in tool_results:
            messages.append(tr)
    return messages
