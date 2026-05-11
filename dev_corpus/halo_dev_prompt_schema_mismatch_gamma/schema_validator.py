def validate_tool_result(msg):
    required = ["role", "tool_call_id", "output"]
    for field in required:
        if field not in msg:
            return {"valid": False, "error": f"Missing field: {field}"}
    return {"valid": True}

def validate_messages(messages):
    for msg in messages:
        if msg.get("role") == "tool":
            result = validate_tool_result(msg)
            if not result["valid"]:
                return result
    return {"valid": True}
