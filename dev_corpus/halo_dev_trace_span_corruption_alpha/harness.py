from pipeline import Pipeline

def run(query):
    p = Pipeline()
    result = p.run(query)
    trace = result["trace"]
    # Verify causal ordering: each span should be child of previous
    for i in range(1, len(trace)):
        if trace[i]["parent_id"] != trace[i-1]["span_id"]:
            return {"ok": False, "error": "trace ordering broken"}
    return {"ok": True, "response": result["response"]}
