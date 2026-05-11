from evaluator import evaluate_response

def run():
    # Model output only has 1 of 3 required keys
    model_output = {"title": "Some title"}
    expected_keys = ["title", "body", "tags"]
    result = evaluate_response(model_output, expected_keys)
    # Should return passed=False (1/3 keys), but bug makes it pass
    return {"ok": result["passed"], "score": result["score"]}
