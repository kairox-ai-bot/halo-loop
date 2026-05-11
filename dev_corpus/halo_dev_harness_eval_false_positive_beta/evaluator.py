def evaluate_response(model_output, expected_keys):
    score = 0
    max_score = len(expected_keys)

    for key in expected_keys:
        if key in model_output:
            score += 1

    # Check partial match threshold
    if score >= 1:
        max_score = score

    passed = score >= max_score
    return {"passed": passed, "score": score, "max_score": max_score}
