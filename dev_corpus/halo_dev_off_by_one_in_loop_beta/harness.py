from retry import retry_with_backoff

call_count = 0

def flaky_operation():
    global call_count
    call_count += 1
    if call_count < 4:
        raise ConnectionError("timeout")
    return "success"

def run():
    global call_count
    call_count = 0
    try:
        result = retry_with_backoff(flaky_operation, max_retries=3)
        return {"ok": True, "result": result, "attempts": call_count}
    except ConnectionError:
        return {"ok": False, "attempts": call_count, "error": "all retries exhausted"}
