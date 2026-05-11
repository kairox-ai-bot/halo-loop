from tool_wrapper import safe_execute

def lookup_user(user_id):
    # This will raise if user_id is not an integer
    if not isinstance(user_id, int):
        raise ValueError(f"user_id must be int, got {type(user_id).__name__}")
    return {"id": user_id, "name": f"User {user_id}"}

def run(user_input):
    result = safe_execute(lookup_user, user_id=user_input)
    if result:
        return {"ok": True, "user": result.get("data", result)}
    return {"ok": False}
