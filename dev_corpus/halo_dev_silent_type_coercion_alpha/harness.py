from adapter import ToolAdapter

def run(model_output):
    adapter = ToolAdapter()
    # Model returns integer 1 instead of string "001"
    result = adapter.call("fetch_record", record_id=1)
    if result.get("found"):
        return {"ok": True, "record": result}
    return {"ok": False, "url_called": result.get("url_called"), "note": "record not found"}
