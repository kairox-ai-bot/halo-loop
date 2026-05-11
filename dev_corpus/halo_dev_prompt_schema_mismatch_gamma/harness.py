from prompt_builder import build_tool_result, build_messages
from schema_validator import validate_messages

def run(user_query, tool_call_id="tc_1", tool_result_data="search results here"):
    tool_result = build_tool_result(tool_call_id, tool_result_data)
    validation = validate_messages([tool_result])
    if not validation["valid"]:
        return {"ok": False, "error": validation["error"]}
    messages = build_messages(user_query, [tool_result])
    return {"ok": True, "messages": messages}
